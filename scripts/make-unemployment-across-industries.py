import requests
import json
from datetime import datetime, timedelta
import os
import argparse
from pytz import timezone

"""
make-unemployment-across-industries.py for vega-datasets

This script fetches unemployment data across industries from the Bureau of Labor Statistics (BLS) API
and processes it into a structured JSON format for use in the vega-datasets repository, replicating
the originally uploaded version of the dataset. The timestamp for each data point is adjusted
based on Daylight Saving Time (DST) in the United States to match the original json file's timestamps.
By default the script will output to unemployment-across-industries.json in the `data` folder.

Usage:
    python make-unemployment-across-industries.py --api_key YOUR_API_KEY [--output_file OUTPUT_FILE]

Requirements:
    - A BLS API key (v2.0, obtain from https://www.bls.gov/developers/)
    - Python 3.6+
    - requests library (install with 'pip install requests')
    - pytz library (install with 'pip install pytz')

BLS Series IDs:
    Government:                  rate: LNU04028615, count: LNU03028615
    Mining and Extraction:       rate: LNU04032230, count: LNU03032230
    Construction:                rate: LNU04032231, count: LNU03032231
    Manufacturing:               rate: LNU04032232, count: LNU03032232
    Wholesale and Retail Trade:  rate: LNU04032235, count: LNU03032235
    Transportation and Utilities:rate: LNU04032236, count: LNU03032236
    Information:                 rate: LNU04032237, count: LNU03032237
    Finance:                     rate: LNU04032238, count: LNU03032238
    Business services:           rate: LNU04032239, count: LNU03032239
    Education and Health:        rate: LNU04032240, count: LNU03032240
    Leisure and hospitality:     rate: LNU04032241, count: LNU03032241
    Other:                       rate: LNU04032242, count: LNU03032242
    Agriculture:                 rate: LNU04035109, count: LNU03035109
    Self-employed:               rate: LNU04035181, count: LNU03035181
"""

# Constants
API_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
START_YEAR = 2000
END_YEAR = 2010
END_MONTH = 2  # February

# Series order
series_order = ['Government', 'Mining and Extraction', 'Construction', 'Manufacturing',
                'Wholesale and Retail Trade', 'Transportation and Utilities', 'Information',
                'Finance', 'Business services', 'Education and Health', 'Leisure and hospitality',
                'Other', 'Agriculture', 'Self-employed']

# Updated mapping with separate rate and count codes
bls_mapping = {
    'Government': {'rate': 'LNU04028615', 'count': 'LNU03028615'},
    'Mining and Extraction': {'rate': 'LNU04032230', 'count': 'LNU03032230'},
    'Construction': {'rate': 'LNU04032231', 'count': 'LNU03032231'},
    'Manufacturing': {'rate': 'LNU04032232', 'count': 'LNU03032232'},
    'Wholesale and Retail Trade': {'rate': 'LNU04032235', 'count': 'LNU03032235'},
    'Transportation and Utilities': {'rate': 'LNU04032236', 'count': 'LNU03032236'},
    'Information': {'rate': 'LNU04032237', 'count': 'LNU03032237'},
    'Finance': {'rate': 'LNU04032238', 'count': 'LNU03032238'},
    'Business services': {'rate': 'LNU04032239', 'count': 'LNU03032239'},
    'Education and Health': {'rate': 'LNU04032240', 'count': 'LNU03032240'},
    'Leisure and hospitality': {'rate': 'LNU04032241', 'count': 'LNU03032241'},
    'Other': {'rate': 'LNU04032242', 'count': 'LNU03032242'},
    'Agriculture': {'rate': 'LNU04035109', 'count': 'LNU03035109'},
    'Self-employed': {'rate': 'LNU04035181', 'count': 'LNU03035181'}
}

def is_dst(dt):
    eastern = timezone('US/Eastern')
    aware_dt = eastern.localize(dt)
    return aware_dt.dst() != timedelta(0)

def fetch_bls_data(series_ids, api_key):
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({
        "seriesid": series_ids,
        "startyear": str(START_YEAR),
        "endyear": str(END_YEAR),
        "registrationkey": api_key
    })

    response = requests.post(API_URL, data=data, headers=headers)
    return json.loads(response.text)

def process_bls_data(json_data):
    processed_data = {}
    for series in json_data['Results']['series']:
        series_id = series['seriesID']

        # Find the corresponding series name
        for series_name, codes in bls_mapping.items():
            if series_id in codes.values():
                data_type = 'rate' if series_id == codes['rate'] else 'count'
                break
        else:
            continue  # Skip if series_id not found in mapping

        for item in series['data']:
            year = int(item['year'])
            month = int(item['period'][1:])  # Convert 'M01' to 1, 'M02' to 2, etc.

            # Only process data up to February 2010
            if year == END_YEAR and month > END_MONTH:
                continue

            value = float(item['value'])
            
            # Determine the correct hour based on DST
            dt = datetime(year, month, 1)
            hour = 7 if is_dst(dt) else 8
            date = dt.replace(hour=hour).isoformat() + '.000Z'

            key = (series_name, year, month)
            if key not in processed_data:
                processed_data[key] = {
                    "series": series_name,
                    "year": year,
                    "month": month,
                    "date": date
                }

            if data_type == 'rate':
                value = int(value) if value.is_integer() else value
            else:  # count
                value = int(value)
            
            processed_data[key][data_type] = value

    return list(processed_data.values())

def order_data(data):
    series_order_dict = {series: index for index, series in enumerate(series_order)}
    return sorted(data, key=lambda x: (series_order_dict[x['series']], x['year'], x['month']))

def main(api_key, output_file):
    # Get all series IDs from the mapping
    series_ids = [code for codes in bls_mapping.values() for code in codes.values()]

    # Fetch data from BLS API
    print("Fetching data from BLS API...")
    raw_data = fetch_bls_data(series_ids, api_key)

    # Process the raw data
    print("Processing raw data...")
    processed_data = process_bls_data(raw_data)

    # Order the processed data
    print("Ordering processed data...")
    ordered_data = order_data(processed_data)

    # Reorder the data to match the specified order
    reordered_data = []
    for item in ordered_data:
        reordered_item = {
            "series": item["series"],
            "year": item["year"],
            "month": item["month"],
            "count": item.get("count", None),  # Use get() to handle missing keys
            "rate": item.get("rate", None),   # Use get() to handle missing keys
            "date": item["date"]
        }
        reordered_data.append(reordered_item)

    # Construct the path to the data folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(root_dir, 'data')
    
    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Construct the full path for the output file
    output_path = os.path.join(data_dir, output_file)

    # Write to JSON file
    print(f"Creating JSON file: {output_path}")
    json_output = json.dumps(reordered_data, separators=(',', ':'))

    # Save JSON file
    with open(output_path, 'w', newline='') as f:
        f.write(json_output + '\n')

    print(f"Data has been processed and saved to '{output_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate unemployment across industries data for vega-datasets")
    parser.add_argument("--api_key", required=True, help="BLS API key")
    parser.add_argument("--output_file", default="unemployment-across-industries.json", help="Output JSON file name")
    args = parser.parse_args()

    main(args.api_key, args.output_file)