# '%%' divides each segment under it into cells
# Each cell is just to test methods from documentation

#Docs for fastf1: https://docs.fastf1.dev/
# %%
import requests

resp = requests.get("https://api.jolpi.ca/ergast/f1/2024/1/results.json")
data = resp.json()
races = data["MRData"]["RaceTable"]["Races"]
races[0]["raceName"]


#Testing requested data
# %%
for r in races[0]["Results"][:20]:
    print(r["position"], r["Driver"]["familyName"], r["Constructor"]["name"], r["points"])


#Saving data locally using cache
# %%
import fastf1
fastf1.Cache.enable_cache("cache")
session = fastf1.get_session(2024, "Monza", "R")
session.load()
session.results[["Abbreviation", "Position", "GridPosition", "Points", "Status"]]
# %%
