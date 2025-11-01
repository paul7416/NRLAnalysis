from sqlite_wrapper import SQLiteWrapper
""" This is a module to assess all of the games that have been imported and correct the incorrect scores to match the points scored by the below on-field actions. There were some games prior to 2013 where the json had conflicting info between who scored points and what the total team points were. The sum of individual points proved to be correct"""
def get_games(wrapper):
    query = """SELECT id FROM games WHERE complete = 1;"""
    output = wrapper.fetch_all(query)
    return [x[0] for x in output]
def get_nrl_stats(wrapper):
    query = """SELECT games.id, team_id, stat_type, SUM(value)
            FROM nrl_ps
            JOIN player_performance ON nrl_ps.player_performance_id = player_performance.id
            JOIN games ON games.id = player_performance.game_id
            WHERE (stat_type = "tries" 
                OR stat_type = "conversions"
                OR stat_type = "fieldGoals"
                OR stat_type = "goals"
                OR stat_type = "penaltyGoals"
                OR stat_type = "twoPointFieldGoals")
            GROUP BY games.id,team_id, stat_type;"""
    data = wrapper.fetch_all(query)
    output = {}
    for line in data:
        output[line[0]] = []
    for line in data:
        output[line[0]].append(line[1:])
    return output

def match_scores(calced_scores, recorded_scores):
    if not sorted(list(calced_scores.keys())) == sorted(list(recorded_scores.keys())):
        return False

    for key, item in calced_scores.items():
        if recorded_scores[key] != item:
            return False

    return True
def set_game_scores(game, scores, wrapper):
    query = """UPDATE game_teams SET score = ?, conceded = ? WHERE game_id = ? AND team_id = ?;"""
    team_ids = list(scores.keys())
    team_id0 = team_ids[0]
    team_id1 = team_ids[1]
    score_0 = scores[team_id0]
    score_1 = scores[team_id1]
    parameters =  [(score_0, score_1, game, team_id0),
                   (score_1, score_0, game, team_id1)]
    wrapper.execute_many(query, parameters)
    
def analyze_game(game, wrapper, nrl_recorded_scores, nrl_stats):
    action_score = {
            'conversions':2, 
            'fieldGoals': 1,
            'goals': 2,
            'penaltyGoals': 2,
            'tries': 4,
            'twoPointFieldGoals': 1 # 1 point as they record it as both a field goal and 2p field goal
            }
    data = nrl_stats[game]
    team_ids = list(set([x[0] for x in data]))
    scores = {x:0 for x in team_ids}
    for line in data:
        scores[line[0]] += int(line[2] * action_score[line[1]])

    if not match_scores(scores, nrl_recorded_scores[game]):
        print(f"Game:{game}  team {team_ids[0]:2d} calculated_score:{scores[team_ids[0]]:3d} nrl_score:{nrl_recorded_scores[game][team_ids[0]]:3d}")
        print(f"Game:{game}  team {team_ids[1]:2d} calculated_score:{scores[team_ids[1]]:3d} nrl_score:{nrl_recorded_scores[game][team_ids[1]]:3d}")
        print()
        set_game_scores(game, scores, wrapper)


def get_game_scores(wrapper):
    query = """SELECT game_id, team_id, score
            FROM game_teams
            JOIN games ON game_teams.game_id = games.id
            WHERE games.complete is 1;"""
    raw_data = wrapper.fetch_all(query)
    nrl_raw_scores = {}
    for item in raw_data:
        nrl_raw_scores[item[0]] = {}
    for item in raw_data:
        nrl_raw_scores[item[0]][item[1]] = item[2]
    return nrl_raw_scores

def return_points_from_scores(scores):
    ids = list(scores.keys())
    if scores[ids[0]] > scores[ids[1]]:
        return [(ids[0],2), (ids[1],0)]
    elif scores[ids[0]] < scores[ids[1]]:
        return [(ids[0],0), (ids[1],2)]
    return [(ids[0],1), (ids[1],1)]

def update_winners(wrapper, nrl_recorded_scores):
    parameters = []
    query = """UPDATE game_teams SET comp_points = ?
                    WHERE game_id = ?
                    AND team_id = ?;"""
    for key, item in nrl_recorded_scores.items():
        comp_points = return_points_from_scores(item)
        parameters.append((comp_points[0][1], key, comp_points[0][0]))
        parameters.append((comp_points[1][1], key, comp_points[1][0]))
    wrapper.execute_many(query, parameters)


    


wrapper = SQLiteWrapper(db_name = "/home/paul/Projects/NRLAnalysis/database.db")
wrapper.connect()
games = (get_games(wrapper))
nrl_recorded_scores = get_game_scores(wrapper)
nrl_stats = get_nrl_stats(wrapper)
update_winners(wrapper, nrl_recorded_scores)
for game in games[:]:
    analyze_game(game, wrapper, nrl_recorded_scores, nrl_stats)
