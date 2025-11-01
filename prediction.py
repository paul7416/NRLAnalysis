import numpy as np
import json
from sqlite_wrapper import SQLiteWrapper
from db_analysis import Regression
import pandas as pd
import os
import statsmodels.api as sm
import matplotlib.pyplot as plt


class Predictor():
    def __init__(self, start_year, end_year):
        self.start_year = start_year
        self.end_year = end_year
        self.base_folder = "/home/paul/Projects/NRLAnalysis/"
        self.get_data()
        self.add_form()
        self.get_model()

    def log_column(self, column, multiplier):
        new_column = column * multiplier
        absolutes = new_column.abs()
        ve = new_column / absolutes
        return (np.log(absolutes) * ve).fillna(0)


    
    def get_team_form(self, game_id, team, sample_size=5):
        team_games = self.df[((self.df["home"] == team) | (self.df["away"] == team)) & (self.df["game_id"] < game_id)].tail(sample_size)
        if team_games.shape[0] == 0:
            return(0, 0, 0)

        no_games = team_games.shape[0]
        home_games = team_games[(team_games["home"] == team)]
        away_games = team_games[(team_games["away"] == team)]
        avg_home_games = (team_games['home'] == team).sum() / no_games

        avg_residuals = team_games.mean()
        avg_residuals = team_games["residuals"].mean()
        avg_points = team_games["points"].mean()

        return(avg_home_games, avg_points, avg_residuals)

    def get_form(self, game_id):
        home_team = self.df["home"][game_id]
        away_team = self.df["away"][game_id]
        home_form = self.get_team_form(game_id, home_team)
        away_form = self.get_team_form(game_id, away_team)
        self.df.loc[game_id, ["form_home","form_points","form_residuals"]] += home_form
        self.df.loc[game_id, ["form_home","form_points","form_residuals"]] -= away_form

    def add_form(self):
        for game_id in range(15, self.df.shape[0]):
            self.get_form(game_id)
        self.df = self.df.tail(self.df.shape[0] - 16)

    def get_model(self):
        self.df["const"] = 1
        self.df["home_win"] = self.df["points"] > 0
        params = ["const","form_points", "form_residuals"]
        train = self.df.iloc[:-40]   # First 700 rows for training
        test = self.df.iloc[-40:]    # Remaining rows for testing
        X_train = train[params]
        y_train = train["points"]

        X_test = test[params]
        y_test = test["points"]

        model = sm.OLS(y_train, X_train).fit()
        print(model.summary())
        y_pred = model.predict(X_test)
        test['score_predicted'] = y_pred
        print(test.tail(50))
        test.plot.scatter(x='score_predicted', y='points', title='Scatter Plot')
        plt.show()


    def get_data(self):
        model_folder = os.path.join(self.base_folder, "models")
        filename = os.path.join(model_folder,f"{self.start_year}_{self.end_year}.json")
        with open(filename,"r") as f:
            model_data = json.load(f)
        params = (model_data["params"])
        param_names = list(params.keys())
        data_source = Regression()
        self.df = data_source.get_all_deltas(self.start_year, self.end_year, param_names)
        X = self.df[param_names]
        coefs = pd.Series(params)
        predictions = X.dot(coefs)
        self.df["predicted"] = predictions
        self.df["residuals"] = self.df["points"] - predictions
        self.df["form_points"] = 0
        self.df["form_residuals"] = 0
        self.df["form_home"] = 0



p = Predictor(2018, 2025)
        


