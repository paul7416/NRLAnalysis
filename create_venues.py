from sqlite_wrapper import SQLiteWrapper
import json
import csv

def load_venue(sqlitewrapper, rlp_id, venue_data):
    query = "INSERT INTO venues (name, rlp_id, latitude, longitude) VALUES (?, ?, ?, ?);"
    parameters = (venue_data["name"], rlp_id, venue_data["latitude"], venue_data["longitude"])
    sqlitewrapper.execute_query(query, parameters)
    query = "SELECT MAX(id) FROM venues;"
    pk = sqlitewrapper.fetch_one(query)[0]
    ff_venues = venue_data.get("ff_venue_id")
    if not ff_venues:
        return
    for id in ff_venues.split():
        query = "INSERT INTO venue_linker (venue_id, ff_venue_id) VALUES (?, ?);"
        parameters = (pk, int(id))
        sqlitewrapper.execute_query(query, parameters)





sqlitewrapper = SQLiteWrapper(db_name = "/home/paul/Projects/NRLAnalysis/database.db")
sqlitewrapper.connect()

with open("venues.json","r") as f:
    venue_data = json.load(f)
for key, item in venue_data.items():
    load_venue(sqlitewrapper, key, item)

with open('venue_linker.csv','r') as f:
    csvreader = csv.reader(f, delimiter='|')
    links = list(csvreader)
query = """INSERT INTO nrl_venue_linker (nrl_name, venue_id) VALUES (?, ?);"""
sqlitewrapper.execute_many(query, links)
    






