import sys
import json
import os
from datetime import datetime
from geopy.distance import geodesic
sys.path.append("../")
from sqlite_wrapper import SQLiteWrapper
from header_data_extraction import MatchExtraction

class Importer():
    def __init__(self):
        self.completed_folder = "/home/paul/Projects/NRLAnalysis/nrlstats/data/Completed"
        self.scheduled_folder = "/home/paul/Projects/NRLAnalysis/nrlstats/data/Scheduled"
        self.wrapper = SQLiteWrapper(db_name = "/home/paul/Projects/NRLAnalysis/database.db")
        self.wrapper.connect()
        self.get_players()
        self.get_loaded_games()
        self.match_extraction = MatchExtraction(self.wrapper)

    def get_players(self):
        query = "SELECT id, ff_player_id FROM players;"
        players = self.wrapper.fetch_all(query)
        self.players_link = {x[1]:x[0] for x in players}

    def create_game(self, header_data):
        query = "INSERT INTO games (nrl_stats_loaded, round, year, date, time, match_of_round, venue_id, complete, weather, ff_game_id, ground_conditions) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        parameters = (
                header_data['roundNumber'],
                header_data['year'],
                header_data['date'],
                header_data['time'],
                header_data['match_of_round'],
                header_data['venue'],
                header_data['complete'],
                header_data['weather'],
                header_data['ff_game_id'],
                header_data['ground_conditions']
                )
        self.wrapper.execute_query(query, parameters)
        database_id = self.wrapper.get_max_index('games')
        self.create_game_teams(header_data, database_id)
        return database_id

    def create_game_teams(self, header_data, database_id):
        WIN_POINTS, DRAW_POINTS, LOSS_POINTS = 2, 1, 0
        home_score = header_data['home_score']
        away_score = header_data['away_score']
        if home_score > away_score:
            home_comp_points, away_comp_points = WIN_POINTS, LOSS_POINTS
        elif away_score > home_score:
            home_comp_points, away_comp_points = LOSS_POINTS, WIN_POINTS
        else:
            home_comp_points, away_comp_points = DRAW_POINTS, DRAW_POINTS

        query = """INSERT INTO game_teams (
                                        game_id, 
                                        team_id, 
                                        is_home_team, 
                                        comp_points,
                                        travel_distance,
                                        score,
                                        conceded) 
                                    VALUES(?, ?, ?, ?, ?, ?, ?);"""

        home_distance = self.match_extraction.get_distance(header_data['home_id'], header_data['venue'])
        away_distance = self.match_extraction.get_distance(header_data['away_id'], header_data['venue'])
        home_parameters = (
                database_id,
                header_data['home_id'],
                1,
                home_comp_points,
                home_distance,
                home_score,
                away_score
                )
        away_parameters = (
                database_id,
                header_data['away_id'],
                0,
                away_comp_points,
                away_distance,
                away_score,
                home_score
                )
        self.wrapper.execute_many(query, [home_parameters, away_parameters])


    def update_game(self, header_data, game_key):
        database_id = self.loaded_games[game_key]
        
        query = "UPDATE games SET weather = ?, ground_conditions = ?, nrl_stats_loaded = 1 WHERE id = ?;"
        parameters = (
                header_data['weather'],
                header_data['ground_conditions'],
                database_id
                )
        return database_id




    def get_loaded_games(self):
        query = "SELECT ff_game_id, year, id, complete FROM games;"
        loaded_games = self.wrapper.fetch_all(query)
        self.loaded_games = {f"{x[1]}{x[0]}":{'id':x[2], 'complete':x[3]} for x in loaded_games}

    def load_game(self, filename, game_data):
        # load game data
        match_data = game_data.get('match', '')
        if match_data == '':
            print(f"{filename} is missing header data")
            return
        header_data = self.match_extraction.get_match_data(match_data, filename)
        if None in header_data.values():
            print(header_data)
            return
        game_key = f"{header_data['year']}{header_data['ff_game_id']}"
        if game_key not in self.loaded_games.keys():
            game_id = self.create_game(header_data)
        else:
            game_id = self.update_game(header_data, game_key)

        if not header_data['complete']:
            return
    
        self.load_player_performances(game_id, header_data['home_id'], 'homeTeam', match_data)
        self.load_player_performances(game_id, header_data['away_id'], 'awayTeam', match_data)
        self.load_player_stats(match_data, header_data['home_id'], 'homeTeam', game_id, header_data)
        self.load_player_stats(match_data, header_data['away_id'], 'awayTeam', game_id, header_data)
        return game_id

    def create_player(self, player_data):
        query = """INSERT INTO players
                (ff_player_id, first_name, last_name)
                VALUES (?, ?, ?);"""
        parameters = (player_data['playerId'], player_data['firstName'], player_data['lastName'])
        self.wrapper.execute_query(query, parameters)
        db_id = self.wrapper.get_max_index('players')
        self.players_link[player_data['playerId']] = db_id
        return db_id
       
    def load_player_performances(self, game_id, team_id, team_key, match_data):
        query = """INSERT INTO player_performance 
            (game_id, team_id, player_id, position) 
            VALUES (?, ?, ?, ?);"""
        parameters = []

        for player in match_data[team_key]['players']:
            if player['playerId'] not in self.players_link:
                player_id = self.create_player(player)
            else:
                player_id = self.players_link[player['playerId']]
            parameters.append((game_id, team_id, player_id, player['position']))

        self.wrapper.execute_many(query, parameters)


            
    def get_player_performances(self, game_id, team_id):
        query = """SELECT player_performance.id, players.ff_player_id
                FROM player_performance
                JOIN players
                ON players.id = player_performance.player_id
                WHERE player_performance.game_id = ?
                AND player_performance.team_id = ?;"""
        parameters = (game_id, team_id)
        player_p = self.wrapper.fetch_all(query, parameters)
        return {x[1]:x[0] for x in player_p}


    def load_player_stats(self, match_data, team_id, team_key, game_id, header_data):
        query = """INSERT INTO nrl_ps
                (player_performance_id, stat_type, value)
                VALUES (?, ?, ?);"""
        ps_parameters = []
        performances = self.get_player_performances(game_id, team_id)
        for player in match_data['stats']['players'][team_key]:
            ff_player_id = player['playerId']
            performance_id = performances[ff_player_id]
            for key, item in player.items():
                if key in ('playerId', 'penalties'):
                    continue
                ps_parameters.append((performance_id, key, item))
        self.wrapper.execute_many(query, ps_parameters)



    def archive_game(self, filename, folder):
        file_path = os.path.join(folder, filename)
        


    def import_game(self, folder, filename):
        file_path = os.path.join(folder, filename)

        try:
            with open(file_path, "r") as f:
                game_data = json.load(f)
        except:
            print(f"error opening or importing {file_path}")
            exit()

        header_data = game_data.get('match','')
        if header_data == '':
            print(f"{filename} does not contain header data")
            return

        match_id = header_data.get('matchId','')

        if match_id == '':
            print(f"{filename} does not contain header data")
            return

        if match_id in self.loaded_games.keys() and self.loaded_games[match_id]['complete']:
            self.archive_game(filename, folder)
            return

        self.load_game(filename, game_data)

    def load_games(self, folder):
        filelist = sorted([x for x in os.listdir(folder) if x.endswith('.json')])
        for filename in filelist[:]:
            print(filename)
            self.import_game(folder, filename)
i = Importer()
i.load_games(i.completed_folder)
#i.load_games(i.scheduled_folder)
