from sqlite_wrapper import SQLiteWrapper
import json
import os
from geopy.distance import geodesic

class Importer():
    def __init__(self):
        self.wrapper = SQLiteWrapper(db_name = "/home/paul/Projects/NRLAnalysis/database.db")
        self.wrapper.connect()
        self.get_venues()
        self.get_teams()
        self.players = self.get_id_dict("ff_player_id", "id", "players")
        self.get_loaded_games()
        self.load_all_games()

    def get_loaded_games(self):
        query = "SELECT year, ff_game_id FROM games;"
        games = self.wrapper.fetch_all(query)
        self.loaded_games = set([f"{x[0]}_{x[1]}.json" for x in games])

    def get_id_dict(self, id_name, key_column_name, table):
        dictionary = {}
        query = f"SELECT {id_name}, {key_column_name} FROM {table};"
        ff_ids = self.wrapper.fetch_all(query)
        for ff_id, db_id in ff_ids:
            dictionary[ff_id] = int(db_id)
        return dictionary

    def get_venues(self):
        self.venues_ff_key = {}
        self.venues = {}
        query = "SELECT venues.id, venue_linker.ff_venue_id, venues.latitude, venues.longitude FROM\
                venues JOIN venue_linker ON venue_linker.venue_id = venues.id;"
        venues_list = self.wrapper.fetch_all(query)
        for row in venues_list:
            self.venues_ff_key[row[1]] = row[0]
            item = {"ff_venue_id": row[1], "latitude": row[2], "longitude": row[3]}
            self.venues[row[0]] = item
        print(self.venues_ff_key)



    def get_teams(self):
        self.teams = {}
        self.teams_ff_key = {}
        query = "SELECT id, ff_team_id, home_venue_id FROM teams;"
        teams_list = self.wrapper.fetch_all(query)
        for row in teams_list:
            self.teams_ff_key[row[1]] = row[0]
            self.teams[row[0]] = row[2]


    
    def create_player(self, performance):
        ff_player_id = int(performance["player_id"])
        query = "INSERT INTO players (ff_player_id, first_name, last_name) VALUES (?, ?, ?);"
        parameters = (
                ff_player_id, 
                performance["first_name"], 
                performance["last_name"])
        self.wrapper.execute_query(query, parameters)
        player_id = self.wrapper.get_max_index("players")
        self.players[ff_player_id] = player_id
        return player_id


    def load_performance(self, game_id, performance, performance_headers, details, start_performance_id, is_home):
        performance_glossary = {
          "T": "tries",
          "TS": "tries_saved",
          "G": "goals",
          "FG": "field_goals",
          "TA": "try_assists",
          "LB": "line_breaks",
          "LBA": "line_break_assists",
          "TCK": "tackles",
          "TB": "tackle_breaks",
          "MT": "missed_tackles",
          "OF": "offloads",
          "ER": "errors",
          "FT": "forty_twenty",
          "FTO": "forced_turnover",
          "MG": "meters_gained",
          "KM": "kick_meters",
          "KD": "kicks_defused",
          "PC": "penalties_conceded",
          "SB": "sin_bins",
          "SO": "send_off",
          "TOG": "minutes_played",
          "FDO": "forced_drop_outs",
          "OFH": "offloads_to_hand",
          "OFG": "offloads_to_ground",
          "SAI": "six_again_infringement",
          "EFIG": "escape_ingoal",
          "FP": "fantasy_points"
        }
        player_id = self.players.get(int(performance["player_id"]))
        if player_id is None:
            player_id = self.create_player(performance)
        team_id = self.teams_ff_key.get(int(performance['squad_id']))
        position = performance["position_match"]
        performance_headers.append((game_id, team_id, player_id, position))
        for key, stat_type in performance_glossary.items():
            count = int(performance.get(key, 0))
            if count:
                details.append((start_performance_id + len(performance_headers), stat_type, count, is_home))


    def load_performances(self, game_id, performances, is_home):
        performance_headers = [] 
        details = []
        player_performance_id = self.wrapper.get_max_index("player_performance")
        if player_performance_id is None:
            player_performance_id = 0

        for performance in performances:
            self.load_performance(game_id, performance, performance_headers, details, player_performance_id, is_home)

        query = "INSERT INTO player_performance (game_id, team_id, player_id, position) VALUES (?, ?, ?, ?);"
        self.wrapper.execute_many(query, performance_headers)
        query = f"INSERT INTO player_stats (player_performance_id, stat_type, count, is_home_team) VALUES (?, ?, ?, ?);"
        self.wrapper.execute_many(query, details)


    def load_all_games(self):
        folder = "/home/paul/Projects/NRLAnalysis/fantasymatches/Completed/"
        files = sorted(os.listdir(folder))
        for file in files[:]:
            print(file)
            if file not in self.loaded_games:
                self.load_game(folder + file)

    def calculate_distance(self, team_id, venue_id):
        team_latitude = self.venues[self.teams[team_id]]["latitude"]
        team_longitude = self.venues[self.teams[team_id]]["longitude"]
        venue_latitude = self.venues[venue_id]["latitude"]
        venue_longitude = self.venues[venue_id]["longitude"]
        coords_1 = (team_latitude, team_longitude)
        coords_2 = (venue_latitude, venue_longitude)
        distance = geodesic(coords_1, coords_2).km
        return distance

    def load_game(self, filepath):
        with open(filepath,"r") as f:
            game_data = json.load(f)
        match_info = game_data["match_info"]
        home_team_players = game_data["home_squad"]
        away_team_players = game_data["away_squad"]

        parameters = []
        parameters.append(int(match_info["round"]))
        parameters.append(int(match_info["year"]))
        date_time = (match_info["match_date"])
        date, time = tuple(date_time.split())
        venue_id = int(self.venues_ff_key[int(match_info["venue_id"])])
        parameters.append(date)
        parameters.append(time)
        parameters.append(match_info["match_id"])
        parameters.append(venue_id)
        parameters.append((match_info["status"] == "complete"))
        parameters.append(match_info["weather"])
        parameters.append(int(match_info["id"]))
        print(parameters)
        query = "INSERT INTO games (round, year, date, time, match_of_round, venue_id, complete, weather, ff_game_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"
        self.wrapper.execute_query(query, parameters)
        game_id = self.wrapper.get_max_index("games")

        home_team_ff_id = int(match_info["home_squad_id"])
        away_team_ff_id = int(match_info["away_squad_id"])
        home_team_id = int(self.teams_ff_key[home_team_ff_id])
        away_team_id = int(self.teams_ff_key[away_team_ff_id])
        home_score = int(match_info["home_score"])
        away_score = int(match_info["away_score"])
        home_comp_points = 0
        away_comp_points = 0
        if home_score > away_score:
            home_comp_points = 2
        elif away_score > home_score:
            away_comp_points = 2
        else:
            away_comp_points = 1
            away_comp_points = 1

        travel_distance_home = self.calculate_distance(home_team_id, venue_id)
        travel_distance_away = self.calculate_distance(away_team_id, venue_id)
        query = "INSERT INTO game_teams (game_id, team_id, is_home_team, comp_points, score, conceded, travel_distance) VALUES (?, ?, ?, ?, ?, ?, ?);";
        parameters_home = (game_id, home_team_id, True, home_comp_points, home_score, away_score, travel_distance_home)
        parameters_away = (game_id, away_team_id, False, away_comp_points, away_score, home_score, travel_distance_away)
        self.wrapper.execute_query(query, parameters_home)
        self.wrapper.execute_query(query, parameters_away)
        self.load_performances(game_id, home_team_players, True)
        self.load_performances(game_id, away_team_players, False)
        
imp = Importer()



        
