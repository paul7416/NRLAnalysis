import os
import json
import time
import datetime
import re
from bs4 import BeautifulSoup






class Scraper():
    def __init__(self):
        self.base_folder = "/home/paul/Projects/NRLAnalysis/odd_scraping/"
        self.html_folder = "raw_html_oddsportal/"
        self.get_name_conversion_dict()
        self.games = []
        self.scrape_all()
        self.save_data()
        print(len(self.games))

    def save_data(self):
        with open(self.base_folder+"odds_data.json", "w") as f:
            json.dump(self.games, f, indent=4)

    def get_name_conversion_dict(self):
        with open(self.base_folder+"name_conversion.json", "r") as f:
            self.name_conversion = json.load(f)

    def get_teams(self, match_string):
        teams = match_string.split("–")
        teams[0] = re.sub(r"[^a-zA-Z ]", "", teams[0])
        teams[0] = re.sub(r" ?OT", "", teams[0])
        teams[0] = self.name_conversion[re.sub("^OT", "", teams[0])]
        teams[1] = re.sub(r"[^a-zA-Z ]", "", teams[1])
        teams[1] = re.sub(r" ?OT", "", teams[1])
        teams[1] = self.name_conversion[re.sub("^OT", "", teams[1])]
        return teams
    def get_odds(self, match_string, away_score):
        odds_string = re.search(r"[0-9\.]+$", match_string).group(0)
        odds_string = odds_string[len(away_score):]
        
        home_odds_match = re.search(r"\d+\.\d\d", odds_string)
        try:
            home_odds = home_odds_match.group(0)
        except AttributeError as e:
            print(f"Odds String = {odds_string}")
            raise(e)


        odds_string = odds_string[len(home_odds):]
        draw_odds = re.search(r"\d+\.\d\d", odds_string).group(0)
        odds_string = odds_string[len(draw_odds):]
        away_odds = re.search(r"\d+\.\d\d", odds_string).group(0)
        return (home_odds, draw_odds, away_odds)

    def get_details(self, match_string):
        score_string = re.search(r"\d+–\d+", match_string).group(0)
        score_strings = score_string.split("–")
        #first score is repeated twice
        score_length = int(len(score_strings[0])/2)
        home_score = score_strings[0][:score_length]
        away_score = score_strings[1]
        teams = self.get_teams(match_string)
        odds = self.get_odds(match_string, away_score)
        details = {
                "home_score": int(home_score), 
                "away_score": int(away_score), 
                "home_team":teams[0], 
                "away_team":teams[1],
                "home_odds":float(odds[0]),
                "draw_odds":float(odds[1]),
                "away_odds":float(odds[2])
                }
        return details


    def analyse_row(self, row, date_string):
        text = str(row.text)
        print(text)
        if "canc." in text or "Pre-season" in text or "Indigenous" in text or "Maori" in text:
            print(text)
            return
        
        text = text.replace(" OT","")
        text = text.replace("Add to my coupon","")
        date_match = re.search(r"\d\d [A-Z][a-z][a-z] \d\d\d\d",text)
        if date_match is not None:
            date_string = date_match.group(0)

        game_match = re.search(r"\d\d:\d\d.+$", text)
        if game_match is None:
            return date_string
        if date_string== None:
            return
        match_string = game_match.group(0)
        time_string = match_string[:5]
        match_string = match_string[5:]
        details = self.get_details(match_string)
        details["date"] = date_string
        details["time"] = time_string
        self.games.append(details)
        #print(details)


        return date_string
        

    def scrape_file(self, filename):
        with open(filename, "r") as f:
            plaintext = f.read()
        soup = BeautifulSoup(plaintext, features="html.parser")
        #print(soup)
        rows = soup.find_all('div', class_="eventRow")
        date_string = None
        for row in rows[:]:
            date_string = self.analyse_row(row, date_string)




    def scrape_all(self):
        folder = self.base_folder+self.html_folder
        file_list = sorted(os.listdir(folder))
        for file in file_list[:]:
            self.scrape_file(folder + file)


s = Scraper()
