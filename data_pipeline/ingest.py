#PROJECT GOALS
#A database (f1.db) holding historical F1 race results
#A script that fetches fresh race data from the internet and fills that database
#A machine learning model trained on that data to predict finishing positions
#A web app that shows those predictions in a browser

#ingest.py covers:
#Extracting data from fastf1 API and storing the results into f1.db
#Latest Extract on 09/12/2026 with the latest extracted race being 11th race of 2026 Season

import requests
import sqlite3
import time

DB_PATH = "f1.db"
BASE_URL = "https://api.jolpi.ca/ergast/f1"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            season INTEGER, round INTEGER, race_name TEXT, circuit_id TEXT,
            date TEXT, driver_id TEXT, constructor_id TEXT,
            grid INTEGER, position INTEGER, points REAL, status TEXT,
            PRIMARY KEY (season, round, driver_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qualifying (
            season INTEGER, round INTEGER, driver_id TEXT,
            quali_position INTEGER,
            PRIMARY KEY (season, round, driver_id)
        )
    """)
    return conn

def fetch_json(url, params=None, max_retries=5):
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 429:
            wait = 5 * (attempt + 1)  # back off progressively: 5s, 10s, 15s...
            print(f"Rate limited on {url}, waiting {wait}s before retrying...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Gave up on {url} after {max_retries} retries")

def season_is_complete(conn, season):
    """A past season's results never change once it's over — skip re-fetching it
    if we already have data for it, UNLESS it's the current calendar year."""
    import datetime
    current_year = datetime.date.today().year
    if season >= current_year:
        return False  # always re-check the current/ongoing season
    cursor = conn.execute("SELECT COUNT(*) FROM results WHERE season = ?", (season,))
    count = cursor.fetchone()[0]
    return count > 0  # already have it, don't touch it again

def ingest_season(conn, season):
    schedule = fetch_json(f"{BASE_URL}/{season}.json")
    races = schedule["MRData"]["RaceTable"]["Races"]

    for race in races:
        rnd = int(race["round"])

        data = fetch_json(f"{BASE_URL}/{season}/{rnd}/results.json")
        race_results = data["MRData"]["RaceTable"]["Races"]
        if race_results:
            for r in race_results[0]["Results"]:
                conn.execute("""
                    INSERT OR REPLACE INTO results
                    (season, round, race_name, circuit_id, date, driver_id,
                     constructor_id, grid, position, points, status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    season, rnd, race["raceName"], race["Circuit"]["circuitId"],
                    race["date"], r["Driver"]["driverId"], r["Constructor"]["constructorId"],
                    int(r["grid"]), int(r["position"]) if r["position"].isdigit() else None,
                    float(r["points"]), r["status"]
                ))

        qdata = fetch_json(f"{BASE_URL}/{season}/{rnd}/qualifying.json")
        quali_results = qdata["MRData"]["RaceTable"]["Races"]
        if quali_results:
            for q in quali_results[0]["QualifyingResults"]:
                conn.execute("""
                    INSERT OR REPLACE INTO qualifying
                    (season, round, driver_id, quali_position)
                    VALUES (?,?,?,?)
                """, (season, rnd, q["Driver"]["driverId"], int(q["position"])))

        conn.commit()
        time.sleep(1.5)  # more conservative pacing, especially important on shared CI IPs

if __name__ == "__main__":
    conn = get_db()
    for yr in range(2018, 2027):
        if season_is_complete(conn, yr):
            print(f"Skipping {yr} — already have complete data.")
            continue
        print(f"Ingesting {yr}...")
        ingest_season(conn, yr)
    conn.close()
    print("Done.")