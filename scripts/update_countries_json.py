#!/usr/bin/env python3
"""
countries.json Dataset Updater

This script updates the countries.json file in the vega-datasets repository
in a manner consistent with a minor release. It fetches current data from 
the source Google Sheets files, processes the data, and then filters the results to  
match the countries and years in the existing dataset. To ensure reproducibility  
and data consistency, the script fetches the existing countries.json dataset 
from a specific commit.

Data sources:
- Google Sheets: Multiple sheets containing updated Gapminder data
- Vega-Datasets: Raw GitHub URL (commit: 05fcb7c07b1d76206856e75129fc1e79dc61735c)

Usage:
    Place this script in the 'scripts' folder of the repository.
    Run it to generate an updated 'countries.json' file in the 'data' folder.

Note:
    The updated countries.json formatting includes spaces for readability.
    The new source dataset has no data for Aruba and changes the country
    name "Hong Kong" to "Hong Kong, China".
"""

import os
import json
import re
from typing import Tuple

import pandas as pd
import requests

# Define the desired time interval between data points
YEAR_INTERVAL = 5

def fetch_google_sheet(sheet_url: str) -> pd.DataFrame:
    """Fetch data from a Google Sheet and return a pandas DataFrame."""
    key_match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
    gid_match = re.search(r'gid=(\d+)', sheet_url)
    if not (key_match and gid_match):
        raise ValueError("Invalid Google Sheets URL")
    
    sheet_key, gid = key_match.group(1), gid_match.group(1)
    csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv&gid={gid}"
    return pd.read_csv(csv_export_url)

def load_datasets() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load datasets from Google Sheets and GitHub."""
    urls = [
        "https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676",  # life expectancy v14
        "https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676",  # fertility v14
    ]
    df_life, df_fertility = [fetch_google_sheet(url) for url in urls]
    
    countries_url = "https://raw.githubusercontent.com/vega/vega-datasets/05fcb7c07b1d76206856e75129fc1e79dc61735c/data/countries.json"
    response = requests.get(countries_url)
    response.raise_for_status()
    df_countries = pd.DataFrame(response.json())
    
    return df_life, df_fertility, df_countries

def prepare_main_dataframe(df_life: pd.DataFrame, df_fertility: pd.DataFrame) -> pd.DataFrame:
    """Prepare and merge the main dataframe."""
    df_main = df_life[['name', 'time', 'Life expectancy ']]
    df_main = df_main.merge(df_fertility[['name', 'time', 'Babies per woman']], on=['name', 'time'])
    
    df_main = df_main.rename(columns={
        'name': 'country',
        'time': 'year',
        'Life expectancy ': 'life_expect',
        'Babies per woman': 'fertility',
    })
    
    df_main['year'] = df_main['year'].astype(int)
    df_main = df_main[df_main['year'].between(1955, 2000) & (df_main['year'] % YEAR_INTERVAL == 0)]
    return df_main.sort_values(['country', 'year'])

def check_year_intervals(df: pd.DataFrame) -> None:
    """
    Check if all intervals between consecutive years for each country are equal to YEAR_INTERVAL.
    Raises a ValueError if any interval is not equal to YEAR_INTERVAL.
    """
    for country in df['country'].unique():
        country_data = df[df['country'] == country]
        year_diffs = country_data['year'].diff().dropna()
        if not all(year_diffs == YEAR_INTERVAL):
            raise ValueError(f"Invalid year interval found for {country}. All intervals should be {YEAR_INTERVAL} years.")

def filter_and_process_data(df_main: pd.DataFrame, df_countries: pd.DataFrame) -> pd.DataFrame:
    """Filter and process the main dataframe."""
    df_countries.loc[df_countries['country'] == 'Hong Kong', 'country'] = 'Hong Kong, China'
    countries_in_original = set(df_countries['country'])
    df_main = df_main[df_main['country'].isin(countries_in_original)].copy()
    
    # Check year intervals before creating p_ and n_ columns
    check_year_intervals(df_main)
    
    df_main['_comment'] = ''
    first_row = df_main.loc[df_main.groupby('country')['year'].idxmin()].iloc[0]
    df_main.loc[first_row.name, '_comment'] = 'Data courtesy of Gapminder.org'
    
    # Create p_ (previous) and n_ (next) columns for fertility and life_expect
    # These columns contain values from the previous and next time points (YEAR_INTERVAL years apart)
    for col in ['fertility', 'life_expect']:
        df_main[f'n_{col}'] = df_main.groupby('country')[col].shift(-1)
        df_main[f'p_{col}'] = df_main.groupby('country')[col].shift(1)
    
    return df_main[['_comment', 'year', 'fertility', 'life_expect', 'p_fertility', 'n_fertility', 'p_life_expect', 'n_life_expect', 'country']]

def main():
    """Main function to execute the script."""
    # Load datasets
    df_life, df_fertility, df_countries = load_datasets()

    # Prepare and process data
    df_main = prepare_main_dataframe(df_life, df_fertility)
    df_final = filter_and_process_data(df_main, df_countries)

    # Convert to list of dictionaries
    data_list = df_final.apply(lambda row: {k: v for k, v in row.items() if pd.notna(v) and not (k == '_comment' and v == '')}, axis=1).tolist()

    # Save to file in the 'data' folder one level up from the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(script_dir, '..', 'data', 'countries.json')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    with open(save_path, 'w') as f:
        json.dump(data_list, f) # add separators=(',', ':')) to match formatting of original version with no spaces
    
    print(f"Updated countries.json has been saved to {save_path}")

if __name__ == "__main__":
    main()