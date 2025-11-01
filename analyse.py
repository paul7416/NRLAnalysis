import json
import requests
import random
import sys
import numpy as np
def simulate_minute(scores, p1, p2, c1, c2):
    score_1 = (random.random() < p1)
    score_2 = (random.random() < p2)
    conversion_1 = (random.random() < c1) and score_1
    conversion_2 = (random.random() < c2) and score_2
    scores[0] += score_1 * 4 + conversion_1 * 2
    scores[1] += score_2 * 4 + conversion_2 * 2
def simulate_game(p1, p2, c1, c2):
    scores = [0,0]
    for minute in range(80):
        simulate_minute(scores, p1, p2, c1, c2)
    return scores[0] - scores[1]


outcomes = []
no_trials = 10000
for i in range(no_trials):
    outcomes.append(simulate_game(float(sys.argv[1]),float(sys.argv[2]), .76, .76))

nparray = np.array(outcomes)
home_wins = np.sum(nparray > 0)
away_wins = np.sum(nparray < 0)
scaled_home_wins = home_wins * no_trials / (home_wins + away_wins)
scaled_away_wins = away_wins * no_trials / (home_wins + away_wins)
home_prob = scaled_home_wins / no_trials
away_prob = scaled_away_wins / no_trials
print(f"{no_trials} trials")
print(f"Home Win:${1/(home_prob - .01):.2f}")
print(f"Away Win:${1/(away_prob - .01):.2f}")

#print(f"Average margin:{np.mean(nparray)}")
home_team_advantage = home_wins/away_wins - 1
#print(f"home team wins {home_team_advantage * 100}% more games")
