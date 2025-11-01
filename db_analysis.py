import matplotlib.pyplot as plt
import sys
from sqlite_wrapper import SQLiteWrapper
import numpy as np
from scipy import stats
import statsmodels.api as sm
import os
import pandas as pd
import copy
import json
from statsmodels.stats.outliers_influence import variance_inflation_factor

class Regression():
    def __init__(self):
        self.base_folder = "/home/paul/Projects/NRLAnalysis/"
        self.wrapper = SQLiteWrapper(db_name = f"{self.base_folder}database.db")


    def get_stat(self, stat, start_year, end_year, home):
        query = '''SELECT
            games.id,
            SUM(player_stats.count)
            FROM games 
            JOIN player_performance ON player_performance.game_id = games.id
            JOIN player_stats ON player_stats.player_performance_id = player_performance.id
            WHERE player_stats.stat_type = ? 
            AND games.year >= ? 
            AND games.year <= ? 
            AND player_stats.is_home_team = ? GROUP BY games.id;''' 
        parameters = (stat, start_year, end_year, home)
        data = self.wrapper.fetch_all(query, parameters)
        return data


    def get_teams(self, start_year, end_year, is_home):
        query = '''SELECT 
            teams.name
            FROM games 
            JOIN game_teams ON games.id = game_teams.game_id
            JOIN teams on teams.id = game_teams.team_id
            WHERE games.year >= ?
            AND games.year <= ? 
            AND game_teams.is_home_team = ?
            GROUP BY games.id;'''
        parameters = (start_year, end_year, is_home)
        data = self.wrapper.fetch_all(query, parameters)
        return data


    def get_points(self, start_year, end_year, is_home):
        query = '''SELECT 
            games.id,
            SUM(game_teams.score)
            FROM games 
            JOIN game_teams ON games.id = game_teams.game_id
            JOIN teams on teams.id = game_teams.team_id
            WHERE games.year >= ?
            AND games.year <= ?
            AND game_teams.is_home_team = ?
            GROUP BY games.id, game_teams.team_id;'''
        parameters = (start_year, end_year, is_home)
        data = self.wrapper.fetch_all(query, parameters)
        return data

    def get_delta_frame(self, data1, data2, statistic):
        df = pd.DataFrame(columns = ['game_id'])
        df = df.merge(pd.DataFrame(data1, columns = ["game_id", "1"]), on=["game_id"], how="outer")
        df = df.merge(pd.DataFrame(data2, columns = ["game_id", "2"]), on=["game_id"], how="outer")
        df=df.fillna(0)
        df[statistic] = df["1"] - df["2"]
        df = df.drop("1", axis=1)
        df = df.drop("2", axis=1)
        return df

    def sm_to_json(self, model, model_name):
        model_summary = {
            'name':model_name,
            'params': model.params.to_dict(),
            'pvalues': model.pvalues.to_dict(),
            'rsquared': model.rsquared,
            'rsquared_adj': model.rsquared_adj,
            'fvalue': model.fvalue,
            'f_pvalue': model.f_pvalue,
            'aic': model.aic,
            'bic': model.bic,
            'nobs': model.nobs
        }
        model_dir = os.path.join(self.base_folder, "models")
        os.makedirs(model_dir, exist_ok=True)

        filename = os.path.join(model_dir, f"{model_name}.json")
        print(filename)
        with open(filename, "w") as f:
            json.dump(model_summary, f, indent=2)


    def get_all_deltas(self, start_year, end_year, params):
        self.wrapper.connect()
        df = pd.DataFrame(columns = ['game_id'])
        for statistic in params[:]:
            home_data = self.get_stat(statistic, start_year, end_year, True)
            away_data = self.get_stat(statistic, start_year, end_year, False)
            delta_frame = self.get_delta_frame(home_data, away_data, statistic)
            df = df.merge(delta_frame, on=["game_id"], how="outer")

        df = df.sort_values(by="game_id").reset_index(drop=True)
        home_teams = list(zip(*self.get_teams(start_year, end_year, True)))[0]
        away_teams = list(zip(*self.get_teams(start_year, end_year, False)))[0]
        df['home'] = home_teams
        df['away'] = away_teams

        home_points = self.get_points(start_year, end_year, True)
        away_points = self.get_points(start_year, end_year, False)
        points_df = self.get_delta_frame(home_points, away_points, "points")
        df = df.merge(points_df, on=["game_id"], how="outer")
        df=df.fillna(0)
        self.wrapper.close()
        return df

    def deltas(self, start_year, end_year):
        params =[
                "forced_drop_outs",
                "kick_meters",
                "line_breaks",
                "meters_gained",
                ]

        df = self.get_all_deltas(start_year, end_year, params)
        #df["const"] = 1
        train = df.iloc[:-80]   # First 700 rows for training
        test = df.iloc[-80:]    # Remaining rows for testing
        #params.append("const")

        X_train = train[params]
        y_train = train["points"]

        X_test = test[params]
        y_test = test["points"]

        model = sm.OLS(y_train, X_train).fit()
        print(model.summary())
        y_pred = model.predict(X_test)
        test['residual'] = y_test - y_pred
        test['predicted'] = y_pred
        print(test[["home","away","points","residual","predicted"]].tail(50))

        home_residuals = test[['home', 'residual']].rename(columns={'home':'team'})
        away_residuals = test[['away', 'residual']].rename(columns={'away':'team'})
        away_residuals['residual'] = -away_residuals['residual']
        team_residuals = pd.concat([home_residuals, away_residuals])
        average_residuals = team_residuals.groupby('team')['residual'].mean().sort_values(ascending=False)
        print(average_residuals)
        print(test['residual'].describe().round(3))
        self.sm_to_json(model, f"{start_year}_{end_year}")




if __name__ == "__main__":
    start_year = int(sys.argv[1])
    end_year = int(sys.argv[2])
    r = Regression()
    r.deltas(start_year,end_year)



