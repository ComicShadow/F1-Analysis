#Importing stuff
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error
from scipy.stats import spearmanr
import xgboost as xgb
import joblib

#Correlation value per race: 0.69

conn = sqlite3.connect("f1.db")
df = pd.read_sql("SELECT * FROM features", conn) #features table stored into df
conn.close()

df = df.dropna(subset=["target_position"]) #Cleaning all null values since there was a bit from 2018 - 2020

#What we will use to make predictions
#Unfortunately does not account for regulation changes and doesn't directly account for car upgrades
feature_cols = [
    "grid", "quali_position", "driver_avg_finish_last5", "driver_avg_points_last5",
    "driver_races_completed", "team_avg_finish_last5", "team_avg_points_last5",
    "driver_avg_finish_this_track",
    "team_points_trend", "team_races_this_season",   # new
]

x = df[feature_cols].copy()
y = df["target_position"]
x = x.fillna(x.mean())

#As of making this project, proficiency is low with scikit learn, so there was use of AI tools to assist

#Split by RACE so all drivers from one race stay together in train or test
#since we are comparing drivers with their previous performances
groups = df["season"].astype(str) + "_" + df["round"].astype(str)
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(x, y, groups))

X_train, X_test = x.iloc[train_idx], x.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

model = xgb.XGBRegressor(
    n_estimators=300, max_depth=4, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
model.fit(X_train, y_train)

preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
print(f"Mean absolute error on held-out races: {mae:.2f} positions")

test_df = df.iloc[test_idx].copy()
test_df["pred"] = preds
correlations = []
for _, race_group in test_df.groupby(["season", "round"]):
    if len(race_group) > 2:
        corr, _ = spearmanr(race_group["target_position"], race_group["pred"])
        correlations.append(corr)
print(f"Average Spearman rank correlation per race: {np.mean(correlations):.2f}")

joblib.dump(model, "model/model.pkl")
joblib.dump(feature_cols, "model/feature_cols.pkl")
joblib.dump(x.mean().to_dict(), "model/fill_values.pkl")
print("Model saved to model/model.pkl")
