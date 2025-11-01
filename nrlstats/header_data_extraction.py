import json
import pytz
from datetime import datetime
from geopy.distance import geodesic
import os

class MatchExtraction():
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.get_venues()
        self.get_venue_links()
        self.get_cities()
        self.get_teams()
        self.data_folder = "/home/paul/Projects/NRLAnalysis/nrlstats/data/Completed"

    def get_venue_links(self):
        query = "SELECT nrl_name, venue_id FROM nrl_venue_linker;"
        loaded_links = self.wrapper.fetch_all(query)
        self.venue_links = {x[0]:x[1] for x in loaded_links}

    def print_venues(self):
        venue_list = []
        for key, value in self.venues.items():
            venue_list.append((key.title(), value['id']))
        venue_list = sorted(venue_list)
        for venue in venue_list:
            print(f"{venue[1]:2} {venue[0]}")

    def capture_int(self, prompt, min_int=0, max_int = float('inf'), max_retries = 5):
        for i in range(max_retries):
            val = input(prompt)
            if val.lower() == 'q' or val.lower() == 'quit':
                return None
            try:
                retval = int(val)
                if retval <= max_int and retval >= min_int:
                    return retval
                print(f"Value must be between {min_int} and {max_int}")
            except ValueError:
                print("Please enter an integer")
        raise ValueError("Maximum retries reached")


    def create_venue_link(self, name):
        self.print_venues()
        id = self.capture_int(f"Select option above for {name}")
        if id is None:
            raise ValueError
        query = "INSERT INTO nrl_venue_linker (nrl_name, venue_id) VALUES (?, ?);"
        parameters = (name, id)
        self.wrapper.execute_query(query, parameters)
        self.venue_links[name] = id


    def get_venues(self):
        query = "SELECT id, name, rlp_id, latitude, longitude FROM venues;"
        loaded_venues = self.wrapper.fetch_all(query)
        self.venues = {
                str.lower(x[1]):{
                    "id":x[0], 
                    "rlp_id":x[2], 
                    } 
                for x in loaded_venues}
        self.coordinates = {x[0]:(x[3], x[4]) for x in loaded_venues}


    def get_cities(self):
        self.cities_file_path = "/home/paul/Projects/NRLAnalysis/nrlstats/cities.json"
        with open(self.cities_file_path, "r") as f:
            self.cities = json.load(f)

    def get_teams(self):
        query = "SELECT id, ff_team_id, home_venue_id FROM teams;"
        teams = self.wrapper.fetch_all(query)
        self.teams = {x[1]:x[0] for x in teams}
        self.team_venues = {x[0]:x[2] for x in teams}

    def dump_cities(self):
        with open(self.cities_file_path, "w") as f:
            json.dump(self.cities, f)

    def get_match_id_data(self, match_data, filename):
        output = {}
        matchId = match_data.get("matchId",'')
        if len(matchId) != 11:
            print(f"{filename} is missing or has a malformed matchId")
            return
        try:
            output['year'] = int(matchId[:4])
            output['ff_game_id'] = int(matchId[4:])
            output['match_of_round'] = int(matchId[-2])
        except ValueError:
            print(f"{filename} has a malformed matchId")
            return
        return output

    def get_round_number(self, match_data, filename):
        roundNumber = match_data.get('roundNumber')
        if not roundNumber:
            print(f"{filename} is missing a valid round number")
            return
        return roundNumber

    def get_venue(self, match_data, filename):
        venue = match_data.get("venue","")
        if venue == "":
            print(f"{filename} is missing a valid venue:")
            return
        if venue not in self.venue_links:
            try:
                self.create_venue_link(venue)
            except:
                print(game_data)
                exit()
        return self.venue_links[venue]

    def get_venue_city(self, match_data, venue, filename):
        if not venue:
            return
        venueCity = match_data.get("venueCity","")
        if venueCity == '': 
            print(f"{filename} is missing a valid venueCity: {match_data['venue']}")
            venueCity = input("Enter city: ")

            match_data['venueCity'] = venueCity
        return venueCity

    def get_distance(self, team_id, venue_id):
        home_venue = self.team_venues[team_id]
        return geodesic(self.coordinates[home_venue], self.coordinates[venue_id]).km



    def get_time_date(self, venueCity, filename, match_data):
        if not venueCity: 
            return None, None
        local_timezone = self.cities.get(venueCity, '')
        if local_timezone == '':

            local_timezone = input(f"Enter timezone for {venueCity} eg 'Australia/Brisbane': ")
            self.cities[venueCity] = local_timezone
            self.dump_cities()

        local_timezone = pytz.timezone(local_timezone)
        startTime = match_data.get('startTime', '')
        if startTime == '':
            print(f"{filename} is missing startTime")
            return None, None
        startTime = startTime.replace('Z','')
        if '.' in startTime:
            startTime = startTime.split('.')[0]
        try:
            dt = datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            print(f"Error parsing start time from {filename}: {startTime}")
            return None, None
        utc_dt = dt.replace(tzinfo=pytz.utc)
        local_dt = utc_dt.astimezone(local_timezone)
        date = local_dt.strftime("%Y-%m-%d")
        time = local_dt.strftime("%H:%M:%S")
        return date, time

    def create_team(self, team_data):
        ff_team_id = team_data.get('teamId', 0)
        nickName = team_data.get('nickName','')
        query = "INSERT INTO teams (ff_team_id, name) VALUES (?, ?);"
        parameters = (ff_team_id, nickName)
        self.wrapper.execute_query(query, parameters)
        query = "SELECT id FROM teams WHERE ff_team_id = ?;"
        parameters = (ff_team_id,)
        team_id = self.wrapper.fetch(query, parameters)
        self.teams[ff_team_id] = team_id

    def get_team(self, key, match_data, filename):
        team_data = match_data.get(key, '')
        if team_data == '':
            print(f"{filename} is missing {key}")
            return None, None

        team_nrl_id = team_data.get("teamId",'')
        if team_nrl_id == '':
            print(f'{filename} is missing "teamId"')
            return None, None

        if team_nrl_id not in self.teams:
            self.create_team(team_data)

        team_id = self.teams.get(team_nrl_id, None)
        score = team_data.get("score", 0)
        return(team_id, score)

    def get_game_status(self, match_data):
        status = match_data.get('matchState','')
        return status == 'FullTime'


    def get_match_data(self, match_data, filename):
        output = self.get_match_id_data(match_data, filename)
        roundNumber = self.get_round_number(match_data, filename)
        venue = self.get_venue(match_data, filename)
        venueCity = self.get_venue_city(match_data, venue, filename)
        home_id, home_score = self.get_team('homeTeam', match_data, filename)
        away_id, away_score = self.get_team('awayTeam', match_data, filename)
        date, time = self.get_time_date(venueCity, filename, match_data)

        output['roundNumber'] = roundNumber
        output['venue'] = venue 
        output['venueCity'] = venueCity 
        output['home_id'] = home_id
        output['home_score'] = home_score
        output['away_id'] = away_id
        output['away_score'] = away_score
        output['date'] = date
        output['time'] = time
        output['weather'] = match_data.get('weather','')
        output['ground_conditions'] = match_data.get('groundConditions','')
        output['complete'] = self.get_game_status(match_data)
        return output

