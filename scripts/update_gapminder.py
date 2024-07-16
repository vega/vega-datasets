"""
Gapminder Dataset Updater

This script updates the gapminder.json file in the vega-datasets repository
in a manner consistent with a minor release. It fetches current data from the source, 
processes it, and then filters the results to match the countries and years in the 
existing dataset. To ensure reproducibility and data consistency, the script fetches 
the existing gapminder dataset from a specific commit.

The generated dataset is used in the following PR:
https://github.com/vega/vega-datasets/pull/580

Data sources:
- Google Sheets: Multiple sheets containing updated Gapminder data
- Vega-Datasets: Raw GitHub URL (commit: 05fcb7c07b1d76206856e75129fc1e79dc61735c)

"""

import pandas as pd
import json
import re

def google_sheet_to_pandas(sheet_url):
    key_match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
    gid_match = re.search(r'gid=(\d+)', sheet_url)
    sheet_key, gid = key_match.group(1), gid_match.group(1)
    csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv&gid={gid}"
    return pd.read_csv(csv_export_url)


# Gapminder datasets (as of July 2024) are stored in individual Google Sheets files.
# These files are linked from dataset-specific reference pages:
#   - Life Expectancy: https://www.gapminder.org/data/documentation/gd004/
#   - Population: https://www.gapminder.org/data/documentation/gd003/
#   - Fertility: https://www.gapminder.org/data/documentation/gd008/
#   - Data Geographies: https://www.gapminder.org/data/geo/

urls = [
    "https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676", #life expectancy v14 (retrieved July 11, 2024)
    "https://docs.google.com/spreadsheets/d/1c1luQNdpH90tNbMIeU7jD__59wQ0bdIGRFpbMm8ZBTk/edit?gid=176703676#gid=176703676", #population v7 (retrieved July 11, 2024)
    "https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676", #fertility v14 (retrieved July 11, 2024)
    "https://docs.google.com/spreadsheets/d/1qHalit8sXC0R8oVXibc2wa2gY7bkwGzOybEMTWp-08o/edit?gid=1597424158#gid=1597424158" #data geographies v2 (retrieved July 11, 2024)
]

# Load dataframes from Google Sheets
df_life, df_pop, df_fert, df_region = [google_sheet_to_pandas(url) for url in urls]

# Load gapminder dataset directly from the raw GitHub URL
gapminder_url = "https://raw.githubusercontent.com/vega/vega-datasets/05fcb7c07b1d76206856e75129fc1e79dc61735c/data/gapminder.json"
df_gapminder = pd.read_json(gapminder_url)

# Prepare main dataframe
df_main = df_pop[['name', 'time', 'Population']].rename(columns={'Population': 'pop'})

# Merge other dataframes
df_main = df_main.merge(df_life[['name', 'time', 'Life expectancy ']], on=['name', 'time'])
df_main = df_main.merge(df_fert[['name', 'time', 'Babies per woman']], on=['name', 'time'])
df_main = df_main.merge(df_region[['name', 'six_regions']], on='name')

# Rename columns
df_main = df_main.rename(columns={
    'name': 'country',
    'time': 'year',
    'Life expectancy ': 'life_expect',
    'Babies per woman': 'fertility',
    'six_regions': 'region'
})

# Reorder columns
df_main = df_main[['year', 'country', 'region', 'pop', 'life_expect', 'fertility']]

# Convert year to int and filter years from 1955 to 2005 in increments of 5
df_main['year'] = df_main['year'].astype(int)
df_main = df_main[df_main['year'].between(1955, 2005) & (df_main['year'] % 5 == 0)]

# Sort the dataframe
df_main = df_main.sort_values(['country', 'year'])

# Create the cluster mapping
cluster_map = {
    'south_asia': 0,
    'europe_central_asia': 1,
    'sub_saharan_africa': 2,
    'america': 3,
    'east_asia_pacific': 4,
    'middle_east_north_africa': 5
}

# Add cluster column and drop region column
df_main['cluster'] = df_main['region'].map(cluster_map)
df_main = df_main.drop('region', axis=1)

# Reorder columns
column_order = ['year', 'country', 'cluster', 'pop', 'life_expect', 'fertility']
df_main = df_main[column_order]

# Rename Hong Kong to Hong Kong, China in df_gapminder
df_gapminder.loc[df_gapminder['country'] == 'Hong Kong', 'country'] = 'Hong Kong, China'

# Get the list of countries in df_gapminder
gapminder_countries = set(df_gapminder['country'])

# Keep only rows in df_main that have a country in gapminder_countries
df_main = df_main[df_main['country'].isin(gapminder_countries)]

# Convert population to integer to match data type of original version of the dataset (and handle potential errors)
df_main['pop'] = df_main['pop'].astype(int, errors='ignore')

# Convert DataFrame to list of dictionaries
data_list = df_main.to_dict(orient='records')

# Convert the list of dictionaries to JSON
json_data = json.dumps(data_list)

print(json_data)
with open('gapminder.json', 'w') as f:
    json.dump(data_list, f)