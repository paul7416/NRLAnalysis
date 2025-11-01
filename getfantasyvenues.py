import json
import os

def get_venue_fantasy(filename, venues):
    with open(filename, "r") as f:
        data = json.load(f)
    match_info = data["match_info"]
    venue_id = match_info["venue_id"]
    if venue_id not in venues:
        venues[venue_id] = {
                "match_id":match_info["match_id"],
                "match_date": match_info["match_date"],
                "home_squad": match_info["home_squad_name"],
                "away_squad": match_info["away_squad_name"],
                "venue_id": venue_id,
                "venue_name":match_info["venue_name"]
                }


def get_venues_fantasy(folder, venue_matches):
    games = os.listdir(folder)
    for f in games[:]:
        filename = folder + f
        get_venue_fantasy(filename, venue_matches)
    return venue_matches

def get_venue_rlp(filename, venue_matches_dict):
    with open(filename, "r") as f:
        data = json.load(f)
    date_time = f"{data['date']} {data['time']}:00"
    output = {
             "venue_id": data["venue_id"],
             "home_team": data["home team"],
             "away_team": data["away team"]
             }
    if not venue_matches_dict.get(date_time):
        venue_matches_dict[date_time] = [] 
    venue_matches_dict[date_time].append(output)

def get_venues_rlp(folder, venue_matches_list):
    games = os.listdir(folder)
    for f in games[:]:
        filename = folder + f
        get_venue_rlp(filename, venue_matches_list)
    return venue_matches_list

def find_matching_game(fantasy_match, rlp_matches, linking_dict):
    rlp_match_list = rlp_matches.get(fantasy_match.get("match_date"))
    if rlp_match_list is None:
        return None
    index = 0
    if len(rlp_match_list) > 1:
        print(fantasy_match, rlp_match_list)
        index = int(input("Please enter index of correct match"))
    linking_dict[fantasy_match["venue_id"]] = rlp_match_list[index]["venue_id"]



def match_rlp_fantasy(fantasy_matches, rlp_matches):
    linking_dict = {}
    for item in fantasy_matches.values():
        find_matching_game(item, rlp_matches, linking_dict)
    print(linking_dict)
    with open("venue_linking.json","w") as f:
        json.dump(linking_dict, f, indent=4)

def reverse_linking():
    with open("venue_linking.json","r") as f:
        linking_dict = json.load(f)
    new_linking_dict = {}
    for key, item in linking_dict.items():
        new_linking_dict[item] = key
    with open("venue_linking.json","w") as f:
        json.dump(new_linking_dict, f, indent=4)

def find_rlp_no(linking_list, ffid):
    for pair in linking_list:
        if pair[1] is None:
            continue
        if ffid in pair[1]:
            return True
    return False

def add_ffid_to_rlp_venues():



    with open("venues.json", "r") as f:
        venues_dict = json.load(f)
    for key, item in venues_dict.items():
        ffid = linking_dict.get(key)
        if ffid is None:
            continue
        item["ffid"] = ffid
    with open("venues1.json", "w") as f:
        json.dump(venues_dict, f, indent=4)

def check_rlp_venue(fantasy_venue_matches):
    with open("venues.json", "r") as f:
        rlp_dict = json.load(f)
    linking_list = []
    for key, item in rlp_dict.items():
        linking_list.append((key, item.get("ff_venue_id")))
    for key, game in fantasy_venue_matches.items():
        if not find_rlp_no(linking_list, key):
            print(game)



fantasy_folder = "/home/paul/Projects/NRLAnalysis/fantasymatches/"
#rlp_folder = "/home/paul/Projects/NRLAnalysis/matches/"
completed_subfolder = "Completed/"
scheduled_subfolder = "Scheduled/"
fantasy_venue_matches = get_venues_fantasy(fantasy_folder + completed_subfolder, {})
fantasy_venue_matches = get_venues_fantasy(fantasy_folder + scheduled_subfolder, fantasy_venue_matches)
check_rlp_venue(fantasy_venue_matches)
#rlp_venue_matches = get_venues_rlp(rlp_folder + completed_subfolder, {})
##rlp_venue_matches = get_venues_rlp(rlp_folder + scheduled_subfolder, rlp_venue_matches)
#match_rlp_fantasy(fantasy_venue_matches, rlp_venue_matches)
#add_ffid_to_rlp_venues()
