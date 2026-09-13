# F1 Race Predictor
A machine learning app that predicts how each driver will perform in Formula 1 races, using historical results, qualifying data, and in-season car development trends. The data and model refresh automatically after every race weekend, so predictions stay current without any manual work.

## What it does
The app pulls historical F1 race data, looks at features that capture each driver's recent form and each team's competitive trajectory (Ex- last 5 finishes), and trains a model to predict finishing order. A simple web interface lets you browse predictions by season.

## Features
**Automatic data collection** — pulls historical race results and qualifying data from the Jolpica-F1 API  
**Form-based features** — each driver's average finishing position and points over their last 5 races, and the same for their team/car  
**Season selector** — view predictions for any season in the dataset, filtered to only the drivers who actually competed that season  
**Self-updating** — a scheduled GitHub Actions workflow re-fetches new race results, rebuilds features, and retrains the model automatically after each race weekend  
**Free to run** — the entire pipeline and hosting run on free tiers (GitHub Actions + Streamlit Community Cloud), no server costs

## How it works
```
Jolpica-F1 API
      ↓  (data_pipeline/ingest.py)
   f1.db (SQLite)
      ↓  (data_pipeline/build_features.py)
  features table
      ↓  (model/train.py)
   model.pkl (XGBoost)
      ↓  (app/streamlit_app.py)
   Web app (Streamlit)
```
A GitHub Actions workflow [update.yaml](.github/workflows/update.yml) runs this pipeline and commits the refreshed database and model back to the repo, which automatically redeploys the live Streamlit app.

## Tech Used
-  **Python** — data pipeline, modeling, and app
-  **Jolpica-F1 API** — historical race and qualifying data
-  **pandas / NumPy** — data wrangling and feature engineering
-  **XGBoost / scikit-learn** — prediction model and evaluation
-  **Streamlit** — web app front end
-  **SQLite** — local data storage
-  **GitHub Actions** — scheduled automation

## Check it out for yourself!
Link to streamlit web app: https://f1-mid-analysis.streamlit.app/
