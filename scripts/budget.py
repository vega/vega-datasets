import pandas as pd
import json
import os

def generate_budget_data():
    """
    Generates the budget.json data file for the vega-datasets repository
    using the original source from the U.S. Government Publishing Office.
    """
    source_url = "https://www.govinfo.gov/content/pkg/BUDGET-2016-DB/xls/BUDGET-2016-DB-3.xls"
    
    # Construct the path to the 'data' folder (one directory up)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    output_file = os.path.join(data_dir, "budget.json")

    # Read the source Excel file
    source_df = pd.read_excel(source_url)

    # Format numeric columns and 'TQ' with commas
    numeric_cols = [col for col in source_df.columns if col.isdigit()] + ['TQ']
    source_df[numeric_cols] = source_df[numeric_cols].apply(lambda col: col.map(lambda x: f"{x:,}" if pd.notnull(x) else x))

    # Convert DataFrame to JSON
    budget_data = source_df.to_dict(orient='records')

    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Write the JSON data to a file
    with open(output_file, 'w') as f:
        json.dump(budget_data, f, indent=2)

    print(f"Budget data has been generated and saved to {output_file}")

if __name__ == "__main__":
    generate_budget_data()