import sqlite3
import pandas as pd
import numpy as np #New change to account for seasonal changes

def LoadResults(conn):
    return pd.read_sql("""
        SELECT r.*, q.quali_position
        FROM results r
        LEFT JOIN qualifying q
          ON r.season=q.season AND r.round=q.round AND r.driver_id=q.driver_id
        ORDER BY r.season, r.round
    """, conn)

def ComputeTrend(values):
    """Returns the slope of a simple linear fit over a sequence of values —
    positive means improving, negative means declining. Needs at least 2
    points to mean anything; returns 0.0 otherwise."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)
    return slope

def BuildFeatures(df):
    df = df.sort_values(["season", "round"]).reset_index(drop=True)
    rows = []

    for (season, round_), race_df in df.groupby(["season", "round"]):
        for _, row in race_df.iterrows():
            driver = row["driver_id"]
            constructor = row["constructor_id"]
            circuit = row["circuit_id"]

            # only races that happened BEFORE this one — never leak the future
            history = df[
                (df["season"] < season) |
                ((df["season"] == season) & (df["round"] < round_))
            ]

            driver_hist = history[history["driver_id"] == driver].tail(5)
            team_hist = history[history["constructor_id"] == constructor].tail(5)
            track_hist = history[
                (history["driver_id"] == driver) & (history["circuit_id"] == circuit)
            ]

            # --- in-season car development signal ---
            season_history = history[history["season"] == season]
            team_season_hist = season_history[season_history["constructor_id"] == constructor]
            team_points_trend = ComputeTrend(team_season_hist["points"].tolist())
            team_races_this_season = len(team_season_hist)

            #Changes here
            rows.append({
                "season": season, "round": round_, "driver_id": driver,
                "constructor_id": constructor, "circuit_id": circuit,
                "grid": row["grid"],
                "quali_position": row["quali_position"],

                # recent driver form
                "driver_avg_finish_last5": driver_hist["position"].mean(),
                "driver_avg_points_last5": driver_hist["points"].mean(),
                "driver_races_completed": len(driver_hist),

                # recent team/car form
                "team_avg_finish_last5": team_hist["position"].mean(),
                "team_avg_points_last5": team_hist["points"].mean(),

                # track-specific history
                "driver_avg_finish_this_track": track_hist["position"].mean(),

                # car development within the current season
                "team_points_trend": team_points_trend,
                "team_races_this_season": team_races_this_season,

                # what we're trying to predict
                "target_position": row["position"],
            })

    return pd.DataFrame(rows)

if __name__ == "__main__":
    conn = sqlite3.connect("f1.db")
    raw = LoadResults(conn)
    features = BuildFeatures(raw)
    features.to_sql("features", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Built {len(features)} feature rows.")