#PROJECT GOALS
#A database (f1.db) holding historical F1 race results
#A script that fetches fresh race data from the internet and fills that database
#A machine learning model trained on that data to predict finishing positions
#A web app that shows those predictions in a browser

#ingest.py covers:
#Extracting data from fastf1 API and storing the results into f1.db
#Latest Extract on 09/12/2026 with the latest extracted race being 11th race of 2026 Season

import sqlite3
import time
import requests

#Global Vars
DB_PATH = "f1.db"
BASE_URL = "https://api.jolpi.ca/ergast/f1" #for API calls

def GetDB():
    connection = sqlite3.connect(DB_PATH)
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

def FetchJSON(url, params=None):
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()

def ingest_season(conn, season):
    schedule = FetchJSON(f"{BASE_URL}/{season}.json")
    races = schedule["MRData"]["RaceTable"]["Races"]

    for race in races:
        rnd = int(race["round"])

        # --- results ---
        data = FetchJSON(f"{BASE_URL}/{season}/{rnd}/results.json")
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

        # --- qualifying ---
        qdata = FetchJSON(f"{BASE_URL}/{season}/{rnd}/qualifying.json")
        quali_results = qdata["MRData"]["RaceTable"]["Races"]
        if quali_results:
            for q in quali_results[0]["QualifyingResults"]:
                conn.execute("""
                    INSERT OR REPLACE INTO qualifying
                    (season, round, driver_id, quali_position)
                    VALUES (?,?,?,?)
                """, (season, rnd, q["Driver"]["driverId"], int(q["position"])))

        conn.commit()
        time.sleep(0.5)  # be polite to the free API

#Run this file once to add everything to f1.db
if __name__ == "__main__":
    conn = GetDB()
    for yr in range(2024, 2027):
        print(f"Ingesting {yr}...")
        ingest_season(conn, yr)
    conn.close()
    print("Done.")