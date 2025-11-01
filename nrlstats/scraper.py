import requests
import time
import json
import os
from bs4 import BeautifulSoup

class NRLStatsScraper:
    def __init__(self, crawl_delay=5, retries=3, base_folder="/home/paul/Projects/NRLAnalysis/nrlstats", load_scheduled=False):
        self.load_scheduled = load_scheduled
        self.crawl_delay = crawl_delay
        self.retries = retries
        self.last_request = time.time() - crawl_delay
        self.base_api_url = "https://www.nrl.com"
        self.base_folder = base_folder
        self.completed_folder = os.path.join(base_folder, "data/Completed")
        self.scheduled_folder = os.path.join(base_folder, "data/Scheduled")
        self.status_filepath = os.path.join(self.base_folder, "status.json")
        os.makedirs(self.completed_folder, exist_ok=True)
        self.import_status()

    def import_status(self):
        try:
            with open(self.status_filepath, "r") as f:
                self.status = json.load(f)
            if not isinstance(self.status, dict):
                raise ValueError(f"status.json at {self.status_filepath} is malformed: Expected a dictionary")
        except FileNotFoundError:
            raise FileNotFoundError(f"status.json not found at {self.status_filepath}. Create a valid status.json to proceed.")
        except json.JSONDecodeError:
            raise ValueError(f"status.json at {self.status_filepath} is corrupted. Provide a valid JSON file.")
        self.existing_filelist = set(os.listdir(self.completed_folder))

    def save_json(self, data, filename, matchState):
        if matchState == "FullTime":
            filepath = os.path.join(self.completed_folder, filename)
        else:
            filepath = os.path.join(self.scheduled_folder, filename)
            if not self.load_scheduled:
                print("Completed games scraped")
                exit()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        self.existing_filelist.add(filename)
        print(f"Saved data to {filepath}")

    def get_data(self, extension):
        """
        Fetches HTML from a given URL extension and returns BeautifulSoup object.
        Retries up to self.retries times with delays.
        """
        url = self.base_api_url + extension
        print(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        for attempt in range(1, self.retries + 1):
            delay = max(self.crawl_delay - (time.time() - self.last_request), 0)
            time.sleep(delay)
            self.last_request = time.time()

            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return BeautifulSoup(response.text, "html.parser")
                else:
                    print(f"Attempt {attempt}: Received status code {response.status_code}")
            except requests.RequestException as e:
                print(f"Attempt {attempt}: Request failed: {e}")

            time.sleep(self.crawl_delay)

        raise Exception(f"Failed to fetch data from {url} after {self.retries} retries")

    def extract_qdata(self, soup, div_id):
        """
        Extracts and parses JSON from the 'q-data' attribute of a specified div.
        """
        div = soup.find('div', id=div_id)
        if div and div.has_attr('q-data'):
            q_data_str = div['q-data']
            return json.loads(q_data_str)
        else:
            raise ValueError(f"No div with id='{div_id}' and 'q-data' attribute found.")


    def scrape_match_data(self, extension, matchState):
        """
        Fetches match data from a matchCentreUrl and saves it as a JSON file.
        """
        if matchState != "FullTime" and not self.load_scheduled:
            return False
        filename = extension.replace("/", "_")
        filename = filename.replace("_draw_nrl-premiership_", "")
        filename = (filename + ".json").replace("_.json", ".json")
        if filename in self.existing_filelist:
            return True
        soup = self.get_data(extension)
        data = self.extract_qdata(soup, 'vue-match-centre')
        self.save_json(data, filename, matchState)
        return True

    def update_status_round(self, year, round_number, matchState):
        yearstring = str(year)
        if matchState == "FullTime":
            self.status[yearstring]["rounds"].append(round_number)
        else:
            self.status[yearstring]["scheduled_rounds"].append(round_number)
        self.save_status()

    def update_status_year(self, year):
        yearstring = str(year)
        self.status[yearstring]["complete"] = True
        self.save_status()

    def save_status(self):
        with open(self.status_filepath, "w") as f:
            json.dump(self.status, f)

    def get_no_rounds(self, year):
        """
        Fetches the number of regular-season rounds for a given year from the draw page.
    
        Args:
            year (int): The year to fetch rounds for.
    
        Returns:
            int: The number of regular-season rounds in the season.
    
        Raises:
            ValueError: If the draw page cannot be fetched or rounds cannot be parsed.
        """
        extension = f"/draw/?competition=111&round=1&season={year}"
        soup = self.get_data(extension)
        if not soup:
            raise ValueError(f"Failed to fetch draw page for year {year}")
        try:
            data = self.extract_qdata(soup, 'vue-draw')
            rounds = [x['value'] for x in data.get('filterRounds', []) if 'Round' in x.get('name', '')]
            if not rounds:
                raise ValueError(f"No regular-season rounds found in draw data for year {year}")
            return max(rounds)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Failed to parse regular-season rounds for year {year}: {e}")

    def scrape_round(self, year, round_number):
        """
        Scrapes match data for a specific round in a given year.
        """
        is_round_complete = False
        if round_number in self.status[str(year)]["rounds"]:
            print(f"Year {year} Round {round_number} already completed")
            return
        extension = f"/draw/?competition=111&round={round_number}&season={year}"
        soup = self.get_data(extension)
        data = self.extract_qdata(soup, 'vue-draw')

        for fixture in data.get('fixtures', []):
            match_extension = fixture.get('matchCentreUrl')
            matchState = fixture.get('matchState')
            if matchState not in ("Fulltime", "FullTime") and not self.load_scheduled:
                print(matchState, year, round_number, match_extension)
                print("Completed matches loaded")
                print("Scheduled matches not required")
                exit()

            if match_extension:
                self.scrape_match_data(match_extension, matchState)
        self.update_status_round(year, round_number, matchState)
            
    def scrape_year(self, year):
        """
        Scrapes all rounds for a given year.
        """
        yearstring = str(year)
        if yearstring not in self.status:
            self.status[yearstring] = {"complete":False, "rounds":[]}
        #if self.status[yearstring]["complete"]:
        #    print(f"{year} already completed")
        #    return
        total_rounds = self.get_no_rounds(year)
        print(f"Starting scrape for {year} ({total_rounds} rounds)")
        for rnd in range(1, total_rounds + 1):
            print(f"Scraping Round {rnd}")
            self.scrape_round(year, rnd)
        #self.update_status_year(year)

if __name__ == "__main__":
    scraper = NRLStatsScraper(load_scheduled = False)
    for year in range(2010, 2026):
        scraper.scrape_year(year)

