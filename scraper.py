import os
import requests
from bs4 import BeautifulSoup
import time
import re
import datetime
import json

class Scrape():
    def __init__(self):
        self.requests = self.import_requests()
        self.crawl_delay = 5
        self.retry_delay = 30
        self.max_attempts = 30
        self.last_html_request = time.time() - self.crawl_delay

    def import_requests(self):
        from curl_cffi import requests as req
        return req

    def get_html(self, url, headers, attempt=0):
        # If I continue to run into issues with this I should create a queue 
        # with the url etc and rerun at the end of the scrape maybe have less
        # retries
        retries = 30  # Number of retries before giving up
        elapsed_time = time.time() - self.last_html_request
        delay = max((self.crawl_delay - elapsed_time), 0)
        time.sleep(delay)

        for _ in range(retries):
            self.last_html_request = time.time()
            try:
                if headers!=None:
                    response = self.requests.get(url,headers = headers, timeout=10)
                else:
                    response = self.requests.get(url, timeout=10)
                if response.status_code == 200:
                    return BeautifulSoup(response.content, features="html.parser") 
                else:
                    # Log the URL with error status code
                    #self.log_error(url)
                    continue
            except Exception as e:
                #self.log_error(str(e))
                time.sleep(self.retry_delay)
            
            # If all retries fail, log and return False
        self.log_error(f"Failed to extract products from {url} after {retries} retries")
        return False

    def log_error(self, message):
        # Log the error message to a file or any other preferred destination
        print(message)
        error_file = self.config.get_scraping_error_log()
        with open(error_file, "a") as f:
            f.write(message + " ")
            f.write(str(datetime.now()) + "\n")

def get_round_info(soup):
    a = soup.find('th', class_='boldshade')
    year = re.findall(r"\d\d\d\d",a.text)[0]
    try:
        season_round = re.findall(r"(?<=Round )\d+$", a.text)[0]
    except IndexError as e:
        season_round = re.findall(r"(?<=Premiership).+$",a.text)[0]
    return year, season_round

def get_date_from_string(date_string):
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    date_list = date_string.split()
    if len(date_list) != 4:
        raise ValueError (f"Cannot process date string {date_string}")
    day = int(re.sub("[^0-9]","",date_list[1]))
    month = months.index(re.sub("[^a-zA-Z]","",date_list[2])) + 1
    year = int(date_list[3])
    date = datetime.date(year=year, month=month, day=day)
    return date.strftime("%Y-%m-%d")
def get_time_from_string(time_string):
    string_list = time_string.split()
    time_string = string_list[0].strip()
    hour = int(time_string.split(":")[0])
    if "pm" in str.lower(time_string):
        hour +=12
    minute = int(re.sub("[^0-9]","",time_string.split(":")[1]))
    time = datetime.time(hour=hour, minute=minute)
    return time.strftime("%H:%M")

def get_match_info(soup):
    match_info = {}
    a = soup.find('tbody', id="match_info")
    table_rows = a.find_all('tr')
    #get game status
    for row in table_rows:
        if "Status" in row.text:
            match_info["status"] = row.find('td').text.strip()
        if "Referee" in row.text:
            match_info["referee"] = row.find('td').text.strip()
        if "Venue" in row.text:
            atag = str(row.find('a'))
            venue_id = re.findall(r"(?<=venues\/)\d+", atag)[0]
            match_info["venue_id"] = venue_id
        if "Date" in row.text:
            date_string = row.find('td').text.strip()
            match_info["date"] = get_date_from_string(date_string)
        if "Kick Off" in row.text:
            time_string = row.find('td').text.strip()
            match_info["time"] = get_time_from_string(time_string)
        if "Crowd" in row.text:
            crowd = int(row.find('td').text.strip().replace(",",""))
            match_info["crowd"] = crowd

    #print(table_rows)
    return match_info

def get_player_no_from_href(atag):
    player_no_list = re.findall(r"(?<=players\/)\d+", str(atag))
    if not len(player_no_list):
        return None
    return int(player_no_list[0])

def extract_players(row):
    players = row.find_all('td', class_="name")
    try:
        home_player = get_player_no_from_href(players[0])
        away_player = get_player_no_from_href(players[1])
    except IndexError as e:
        print(row)
        raise IndexError(e)


    return(home_player, away_player)

def extract_coaches(row):
    table_data = row.find_all('td')
    coaches = []
    for line in table_data:
        if line.find('a'):
            coaches.append(re.findall(r"(?<=coaches\/)\d+", str(line))[0])

    return tuple(coaches)


def get_teams(soup, status):
    a = soup.find_all('h3')[0].text
    if status != "Completed":
        return [x.strip() for x in a.split("vs.")]

    teams = re.findall(r"[^0-9]+(?= \d+)", a)
    home_team = teams[0].strip()
    away_team = teams[1].replace("def.","")
    away_team = away_team.replace("lost to","")
    away_team = away_team.strip()
    return home_team, away_team

def get_players(soup):
    team_html = soup.find('tbody',id='match_teams')
    if team_html == None:
        return None, None

    players_dict = {"home":[], "away":[]}
    player_list = []
    positions = ["FB", "W1", "C1", "C2", "W2", "FE", "HB", "FR1", "HK", "FR2", "2R1", "2R2", "L", "B1", "B2", "B3", "B4"]
    coaches = {}
    for row in team_html.find_all('tr'):
        header = row.find('th')
        if not header or header.text.strip() == "":
            continue
        position = header.text
        if position != 'HC':
            player_list.append(list(extract_players(row)))
        else:
            home_coach, away_coach = extract_coaches(row)
            coaches["home"] = home_coach
            coaches["away"] = away_coach
    home_players, away_players = zip(*player_list)
    players = zip(positions, home_players, away_players)
    for position in players:
        players_dict['home'].append({"position":position[0],"player_number":position[1]})
        players_dict['away'].append({"position":position[0],"player_number":position[2]})
    return players_dict, coaches

def get_scoretype(existing_scoretype, row):
    header = row.find('th')
    if header.text.strip() == "":
        return existing_scoretype
    return header.text.strip()

def add_goals(scores, team, score):
    if score[0] == None:
        return
    goals, attempts = tuple(score[1].split("/"))
    for i in range(int(goals)):
        scores[team]['G'].append(score[0])
    for i in range(int(attempts)):
        scores[team]['GA'].append(score[0])

def add_score(scores, team, scoretype, score):
    if score[0] == None:
        return
    try:
        n = int(score[1])
    except ValueError:
        n = 1
    if scoretype not in scores[team]:
        scores[team][scoretype] = []
    for i in range(n):
        scores[team][scoretype].append(score[0])
    return
    

def add_score_row(scores, row, scoretype):
    players_html = row.find_all('td', class_='name')
    players = [get_player_no_from_href(x) for x in players_html]
    number_scores = row.find_all('td', class_='n')
    n = [x.text for x in number_scores]
    score_list = list(zip(players, n))
    if not len(score_list):
        return
    if scoretype != "G":
        add_score(scores, "home", scoretype, score_list[0])
        add_score(scores, "away", scoretype, score_list[1])
    else:
        add_goals(scores, "home", score_list[0])
        add_goals(scores, "away", score_list[1])



def add_goal_row(scores, row, scoretype):
    players_html = row.find_all('td', class_='name')
    n_html = row.find_all('td', class_='n')
    if not len(players_html):
        return
    players = [get_player_no_from_href(x) for x in players_html]
    n = [x.text for x in n_html]


def get_scoresheet(soup):
    scores = {
            "home":{'T':[], 'PT':[], 'G':[], 'GA':[], 'FG':[], 'BIN':[], 'OFF':[]},
            "away":{'T':[], 'PT':[], 'G':[], 'GA':[], 'FG':[], 'BIN':[], 'OFF':[]}
            }
    scoresheet_html = soup.find('tbody', id='match_scoresheet')
    if scoresheet_html == None:
        return None
    scoretype = ''
    rows = scoresheet_html.find_all('tr')
    for row in rows[:]:
        scoretype = get_scoretype(scoretype, row)
        add_score_row(scores, row, scoretype)
    return scores
def save_match(match_info):
    filepath = "/home/paul/Projects/NRLAnalysis/matches/"
    if match_info["status"] == "Completed":
        filepath += "Completed/"
    else:
        filepath += "Scheduled"
    filename = filepath + match_info["rlp_no"] + ".json"
    with open(filename, "w") as f:
        json.dump(match_info, f, indent=4)
    with open("/home/paul/Projects/NRLAnalysis/analyzed_list.txt","a") as f:
        f.write(f'{match_info["year"]} Round {match_info["round"]} {match_info["home team"]} vs {match_info["away team"]}\n')
def analyze_match(scraper, url):
    soup = scraper.get_html(url, None)
    rlp_no = re.findall(r"(?<=\/)\d+$", url)[0]
    year, rnd = get_round_info(soup)
    match_info = get_match_info(soup)
    match_info["rlp_no"] = rlp_no
    match_info["year"] = year
    match_info["round"] = rnd
    teams = get_teams(soup, match_info['status'])
    match_info["home team"] = teams[0]
    match_info["away team"] = teams[1]
    players, coaches = get_players(soup)
    match_info["players"] = players
    match_info["coaches"] = coaches
    match_info["scores"] = get_scoresheet(soup)
    save_match(match_info)

def get_match_url(soup):
    return 'https://www.rugbyleagueproject.org/'+re.findall(r"matches\/\d+", str(soup))[0]

def is_match(soup):
    return re.search(r"\/matches\/\d+", str(soup))

def get_matches(scraper, url):
    directory = '/home/paul/Projects/NRLAnalysis/matches/Completed'
    saved_matches = [x.replace(".json","") for x in os.listdir(directory)]
    

    soup = scraper.get_html(url, None)
    links = soup.find_all('a')
    matches = [get_match_url(x) for x in links if is_match(x)]
    for url in matches:
        match_no = re.findall("\d+$", url)[0]
        if match_no not in saved_matches:
            try:
                analyze_match(scraper, url)
            except Exception as e:
                print(f"Match {url} fatal error:{e}")

def get_player_data(scraper, player_no):
    player = {}
    url = f"www.rugbyleagueproject.org/players/{player_no}"
    soup = scraper.get_html(url, None)
    page_content = soup.find("main", id="page_content")
    player["name"] = page_content.find("h1").text
    stats = soup.find("div", class_="stats")
    vitals = stats.find("dl")
    try:
        details = [x.text for x in vitals.find_all('dd')]
        titles = [x.text for x in vitals.find_all('dt')]
    except:
        return player
    try:
        DOB_index = titles.index("Born")
        player["DOB"] = details[DOB_index]
    except ValueError:
        pass
    try:
        POB_index = titles.index("Place Of Birth")
        player["POB"] = details[POB_index]
    except ValueError:
        pass
    return player

def get_venue_data(scraper, venue_no):
    venue = {}
    url = f"www.rugbyleagueproject.org/venues/{venue_no}"
    soup = scraper.get_html(url, None)
    page_content = soup.find('main', id='page_content')
    venue["name"] = page_content.find("h1").text
    content = soup.find('div', id="content")
    try:
        details = [x.text for x in content.find_all('dd')]
        titles = [x.text for x in content.find_all('dt')]
    except:
        return player
    try:
        coordinates_index = titles.index("Coordinates")
        coordinates = details[coordinates_index]
        latitude, longitude = coordinates.split(",")
        venue["latitude"] = float(latitude)
        venue["longitude"] = float(longitude)
    except ValueError:
        pass
    return venue

def save_players(players):
    with open('/home/paul/Projects/NRLAnalysis/players.json', 'w') as f:
        json.dump(players, f, indent=4)

def save_venues(venues):
    with open('/home/paul/Projects/NRLAnalysis/venues.json', 'w') as f:
        json.dump(venues, f, indent=4)

def get_player_list(scraper):
    directory = '/home/paul/Projects/NRLAnalysis/matches/Completed/'
    files = os.listdir(directory)
    player_list = []
    for file in files[:]:
        filename = directory + file
        with open (filename, "r") as f:
            game_data = json.load(f)
        for p in game_data['players']['home']:
            player_list.append(p["player_number"])
        for p in game_data['players']['away']:
            player_list.append(p["player_number"])
    player_list = list(set(player_list))
    no_players = len(player_list)
    with open('/home/paul/Projects/NRLAnalysis/players.json', 'r') as f:
        try:
            players = json.load(f)
        except json.decoder.JSONDecodeError:
            print("can't decode")
            players = {}
    for index,player_no in enumerate(player_list[:]):
        if player_no and str(player_no) not in players:
            print(f"player {player_no} {index} of {no_players}")
            players[player_no] = (get_player_data(scraper, player_no))
            save_players(players)

def get_venue_list(scraper):
    directory = '/home/paul/Projects/NRLAnalysis/matches/Completed/'
    files = os.listdir(directory)
    venue_list = []
    for file in files[:]:
        filename = directory + file
        with open (filename, "r") as f:
            game_data = json.load(f)
            venue_list.append(game_data["venue_id"])
    venue_list = list(set(venue_list))
    no_venues = len(venue_list)
    with open('/home/paul/Projects/NRLAnalysis/venues.json', 'r') as f:
        try:
            venues = json.load(f)
        except json.decoder.JSONDecodeError:
            print("can't decode")
            venues = {}
    for index,venue_no in enumerate(venue_list[:]):
        if venue_no and str(venue_no) not in venues:
            print(f"venue {venue_no} {index + 1} of {no_venues}")
            venues[venue_no] = (get_venue_data(scraper, venue_no))
            save_venues(venues)





scraper = Scrape()
player_list = get_venue_list(scraper)
#url = "http://www.rugbyleagueproject.org/matches/103171"
#analyze_match(scraper, url)
#for year in range(2014, 2020):
    #url = f"https://www.rugbyleagueproject.org/seasons/nrl-{year}/data.html"
    #get_matches(scraper, url)
