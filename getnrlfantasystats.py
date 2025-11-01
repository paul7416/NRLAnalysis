import requests
import time
import json
import os
import shutil

class Scraper():
    def __init__(self, get_schedule=False):
        self.is_get_schedule = get_schedule
        self.crawl_delay = 5
        self.retries = 30
        self.last_request = time.time() - self.crawl_delay
        self.base_folder = "/home/paul/Projects/NRLAnalysis/"
        self.completed_folder = "/fantasymatches/Completed/"
        self.scheduled_folder = "/fantasymatches/Scheduled/"
        self.base_api_url = "https://www.nrlfantasystats.com/includes/"

    def get_data(self, extension, data):
        current_time = time.time()
        delay = max(self.crawl_delay - (current_time - self.last_request), 0)
        time.sleep(delay)
        self.last_request = time.time()
        url = self.base_api_url + extension + ".php"
        print(url, data)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.nrlfantasystats.com",
            "DNT": "1",
            "Sec-GPC": "1",
            "Referer": "https://www.nrlfantasystats.com/matches.php?m=1111050&year=2025",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers"
        }
         
        for _ in range(self.retries):
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    # Attempt to parse JSON
                    json_data = response.json()
                    return(json_data)
                except ValueError as e:
                    print("Response is not JSON. Here's the raw text:")
                    print(response.text)
            else:
                print(f"Request failed with status code {response.status_code}")
                time.sleep(self.crawl_delay)
        raise Exception("Failed to post request {data}")

    def get_match(self, year, match_id):
        payload = {"match_id":match_id, "year":year}
        game_data = self.get_data("get_match_data", payload)
        record_id = game_data['match_info']['record_id']
        if game_data["match_info"]["status"] != "complete" and not self.is_get_schedule:
            exit()
    
        if game_data["match_info"]["status"] == "complete":
            subfolder = self.completed_folder
        else:
            subfolder = self.scheduled_folder
    
        filename = f"{year}_{match_id}.json"
        with open(self.base_folder + subfolder + filename, "w") as f:
            json.dump(game_data, f, indent=2)
    
    def get_matches(self, year, rnd):
        saved_matches = [x.replace('.json','') for x in os.listdir(self.base_folder + self.completed_folder)]
        if self.is_get_schedule:
            saved_matches += [x.replace('.json','') for x in os.listdir(self.base_folder + self.scheduled_folder)]
    
        payload = {"round":rnd, "year":year}
        matches = self.get_data("get_matches", payload)
        for index, m in enumerate(matches):
            if f"{year}_{m['id']}" in saved_matches:
                continue
            print(f"Getting {year} round:{rnd} match:{index + 1}")
            self.get_match(year, m['id'])
    
    def get_rounds(self, year, start_round = 1):
        payload = {"round_type":"NRL", "year":year}
        rounds = self.get_data("get_rounds", payload)
        for rnd in rounds[start_round - 1:]:
            self.get_matches(year, rnd['id'])
    

scraper = Scraper()
scraper.get_rounds('2025', start_round = 10)
