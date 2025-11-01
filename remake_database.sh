rm database.db
sqlite3 database.db < schema.sql
python3 create_venues.py
sqlite3 database.db < load_teams.sql
