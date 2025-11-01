import json
import os

def get_teams(filename, teams):
    with open(filename, 'r') as f:
        game_data = json.load(f)
    match_info = game_data["match_info"]
    teams[match_info["home_squad_id"]] = match_info["home_squad_name"]
    teams[match_info["away_squad_id"]] = match_info["away_squad_name"]
    
directory = "/home/paul/Projects/NRLAnalysis/fantasymatches/Completed"
files = os.listdir(directory)
teams = {}
for file in files:
    filename = directory + "/" + file
    get_teams(filename, teams)
for team_id, team_name in teams.items():
    print(f'INSERT INTO teams (ff_team_id, name) VALUES ({team_id}, "{team_name}");')

