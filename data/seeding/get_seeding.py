import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

FOLDER_PATH = Path(__file__).resolve().parent
CSV_PATH = Path(FOLDER_PATH / "seeding.csv")

def get_fifa_knockout_table(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Target the correct table by checking for the specific broken header token
    target_table = None
    for table in soup.find_all('table', class_='wikitable'):
        if "Third-place teams" in table.text:
            target_table = table
            break
            
    if not target_table:
        print("Table not found.")
        return None

    # Hardcode the clean target columns we actually want to map to the data
    clean_columns = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
        # "Still_Possible", 
        "1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"
    ]
    num_columns = len(clean_columns)
    
    data_rows = []
    for row in target_table.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue
            
        row_data = [cell.text.strip() for cell in cells]
        
        # Slicing Fix: A valid matrix row must contain exactly 11 points of data.
        # Wikipedia occasionally appends hidden styles or reference cells.
        if len(row_data) >= num_columns:
            data_rows.append(row_data[:num_columns]) # Force slice to match our 11 columns
            
    df = pd.DataFrame(data_rows, columns=clean_columns)

    columns_to_merge = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
    merged_data = df[columns_to_merge].replace("", " ").astype(str).agg(" ".join, axis=1)

    df.insert(0, "Advancing_Groups", merged_data)
    df.drop(columns=columns_to_merge, inplace=True)
    
    return df

# Execute
wiki_url = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage"
knockout_df = get_fifa_knockout_table(wiki_url)
print(knockout_df)
knockout_df.to_csv(CSV_PATH, index=False)
