from sqlite_wrapper import SQLiteWrapper
from datetime import datetime
import json
import os

class OddsImporter():
    def __init__(self):
        self.base_folder = "/home/paul/Projects/NRLAnalysis/"
        self.wrapper = SQLiteWrapper(db_name = f"{self.base_folder}database.db")
        self.wrapper.connect()
        self.get_odds()
        self.get_games()
        self.load_odds()
    
    def get_odds(self):
        filename = self.base_folder + "odd_scraping/odds_data.json"
        with open(filename, "r") as f:
            self.odds_data = json.load(f)

    def convert_date(self, date_string):
        date_obj = datetime.strptime(date_string, "%d %b %Y")
        return date_obj.strftime("%Y-%m-%d")

    def get_games(self):
        self.games = {}
        query = "SELECT games.id, home_team.id, home_team.name, away_team.id, away_team.name,\
                games.date \
                FROM games \
                JOIN game_teams home ON games.id = home.game_id AND home.is_home_team = TRUE \
                JOIN game_teams away ON games.id = away.game_id AND away.is_home_team = FALSE\
                JOIN teams home_team ON home.team_id = home_team.id\
                JOIN teams away_team ON away.team_id = away_team.id;"
        data = self.wrapper.fetch_all(query)
        for game in data:
            key_string = f"{game[5]}_{game[2]}_{game[4]}"
            self.games[key_string] = (game[0], game[1], game[3])
            print(key_string)


    def write_to_db(self, parameters):
        query = "UPDATE game_teams SET win_odds = ? WHERE game_id = ? AND team_id = ?;"
        self.wrapper.execute_many(query, parameters)

    def load_odds(self):
        parameters = []
        for item in self.odds_data[:]:
            date_string = self.convert_date(item["date"])
            key = f"{date_string}_{item['home_team']}_{item['away_team']}"
            home_odds = item['home_odds']
            away_odds = item['away_odds']
            game_data = self.games.get(key)
            if game_data is None:
                continue
            game_id = game_data[0]
            home_team_id = game_data[1]
            away_team_id = game_data[2]
            parameters.append((home_odds, game_id, home_team_id))
            parameters.append((away_odds, game_id, away_team_id))
        self.write_to_db(parameters)






OddsImporter()


