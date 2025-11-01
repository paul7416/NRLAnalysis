CREATE TABLE IF NOT EXISTS "venues"(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name VARCHAR(255),
    rlp_id INTEGER,
    latitude REAL,
    longitude REAL);

CREATE TABLE IF NOT EXISTS "venue_linker"(
    venue_id INTEGER NOT NULL,
    ff_venue_id INTEGER NOT NULL,
    FOREIGN KEY(venue_id) REFERENCES venues(id));

CREATE TABLE IF NOT EXISTS "teams"(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    ff_team_id INTEGER NOT NULL,
    name VARCHAR(100),
    home_venue_id INTEGER NOT NULL,
    FOREIGN KEY(home_venue_id) REFERENCES venues(id)
);

CREATE TABLE IF NOT EXISTS "players"(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    ff_player_id INT NOT NULL,
    first_name VARCHAR(30),
    last_name VARCHAR(30));

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    round INTEGER NOT NULL,
    year INTEGER NOT NULL,
    date VARCHAR(30),
    time VARCHAR(30),
    match_of_round INT NOT NULL,
    venue_id INTEGER NOT NULL,
    complete BOOL NOT NULL,
    weather VARCHAR(100),
    ground_conditions VARCHAR(100),
    ff_game_id INTEGER NOT NULL,
    nrl_stats_loaded BOOL NOT NULL DEFAULT 0,
    FOREIGN KEY(venue_id) REFERENCES venues(id)
);

CREATE TABLE IF NOT EXISTS game_teams (
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    is_home_team BOOLEAN NOT NULL,
    comp_points INT,
    travel_distance REAL,
    score INTEGER,
    conceded INTEGER,
    win_odds REAL,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS "player_performance"(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    position varchar(30),
    FOREIGN KEY(game_id) REFERENCES games(id),
    FOREIGN KEY(player_id) REFERENCES players(id),
    FOREIGN KEY(team_id) REFERENCES teams(id));

CREATE TABLE IF NOT EXISTS "nrl_ps"(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    player_performance_id INTEGER NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    value REAL NOT NULL,
    FOREIGN KEY(player_performance_id) REFERENCES player_performance(id)
);
CREATE TABLE IF NOT EXISTS "nrl_venue_linker"(
    nrl_name VARCHAR(50) NOT NULL,
    venue_id INT NOT NULL,
    FOREIGN KEY(venue_id) REFERENCES venues(id)
);


