#Webapp was also out of my scope at the time of working on this, so yeah -_-

import streamlit as st #The plug
import pandas as pd
import sqlite3
import joblib
import os

st.set_page_config(page_title="F1 Race Predictor", page_icon="🏎️")
st.title("🏎️ F1 Race Predictor")

MODEL_DIR = "model"

@st.cache_resource
def load_model():
    model = joblib.load(os.path.join(MODEL_DIR, "model.pkl"))
    feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols.pkl"))
    fill_values = joblib.load(os.path.join(MODEL_DIR, "fill_values.pkl"))
    return model, feature_cols, fill_values

@st.cache_data
def load_all_features():
    conn = sqlite3.connect("f1.db")
    df = pd.read_sql("SELECT * FROM features", conn)
    conn.close()
    return df

model, feature_cols, fill_values = load_model()
features_df = load_all_features()

# --- season selector ---
seasons = sorted(features_df["season"].unique(), reverse=True)
selected_season = st.selectbox("Season", seasons)

season_df = features_df[features_df["season"] == selected_season] #Restricting to a season

st.subheader(f"Predicted order — {selected_season} season (using each driver's most recent race that season)")

# only drivers who actually appear in this season's data
latest_per_driver = (
    season_df.sort_values("round")
    .groupby("driver_id")
    .tail(1)
    .copy()
)

X_pred = latest_per_driver[feature_cols].fillna(pd.Series(fill_values))
latest_per_driver["predicted_position"] = model.predict(X_pred)

result = (
    latest_per_driver[["driver_id", "constructor_id", "predicted_position"]]
    .sort_values("predicted_position")
    .reset_index(drop=True)
)
result.index += 1
result.rename(columns={
    "driver_id": "Driver", "constructor_id": "Team",
    "predicted_position": "Predicted Score (lower = better)"
}, inplace=True)

st.dataframe(result, width="stretch")