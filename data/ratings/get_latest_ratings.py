import pandas as pd
import requests
import datetime
from pathlib import Path

LIVE_DATA_URL = "https://eloratings.net/World.tsv"
TEAM_NAMES_URL = "https://eloratings.net/en.teams.tsv"
FOLDER_PATH = Path(__file__).resolve().parent
OUTPUT_FILE = Path(FOLDER_PATH / f"ratings_{datetime.datetime.now().strftime("%d_%b_%Y").lower()}.csv")
LATEST_CSV = Path(FOLDER_PATH / "ratings_latest.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_elo_data():
    print("Fetching live Elo rankings data...")
    data_response = requests.get(LIVE_DATA_URL, headers=HEADERS)
    if data_response.status_code != 200:
        print(f"Error fetching data file: {data_response.status_code}")
        return

    print("Fetching team name mappings...")
    names_response = requests.get(TEAM_NAMES_URL, headers=HEADERS)
    if names_response.status_code != 200:
        print(f"Error fetching names file: {names_response.status_code}")
        return

    # 1. Parse Data File
    data_lines = [
        line.split("\t") for line in data_response.text.strip().split("\n")
    ]
    df_data = pd.DataFrame(data_lines)[[2,3]].rename(columns={2: "Country_Code", 3: "rating"})

    # 2. Parse Name Mapping File
    name_lines = [
        line.split("\t") for line in names_response.text.strip().split("\n")
    ]
    df_names = pd.DataFrame(name_lines)
    
    # Clean mapping structure: Column 0 = Code, Column 1 = Name
    df_names = df_names.rename(columns={0: "Country_Code", 1: "country"})
    df_names = df_names[["Country_Code", "country"]].drop_duplicates()
    df_names["Country_Code"] = df_names["Country_Code"].str.strip()
    df_names["country"] = df_names["country"].str.strip()

    merged_df = pd.merge(df_data, df_names, on="Country_Code", how="left")

    # Clean up display layout
    cols = ["country", "rating"]
    final_df = merged_df[cols]
    country_mapping = {"CuraÃ§ao" : "Curacao", "Cape Verde" : "Cabo Verde"}
    final_df.loc[:,"country"] = final_df["country"].replace(country_mapping)

    # Save to file
    final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    LATEST_CSV.unlink(missing_ok=True)
    LATEST_CSV.symlink_to(OUTPUT_FILE)

    print(f"\nSuccess! Formatted data saved to '{OUTPUT_FILE}'.")
    print("\nTop 10 Live Table Preview:")
    print(final_df[["country", "rating"]].head(10).to_string(index=False))


if __name__ == "__main__":
    get_elo_data()