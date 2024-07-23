import pandas as pd

def validate_budget_data():
    """
    Validates that the budget data in the vega-datasets repository
    matches the original source from the U.S. Government Publishing Office.
    """
    source_url = "https://www.govinfo.gov/content/pkg/BUDGET-2016-DB/xls/BUDGET-2016-DB-3.xls" # https://www.govinfo.gov/app/details/BUDGET-2016-DB/context
    vega_url = "https://raw.githubusercontent.com/vega/vega-datasets/05fcb7c07b1d76206856e75129fc1e79dc61735c/data/budget.json" # 2015-10-15 Commit

    source_df = pd.read_excel(source_url)
    vega_df = pd.read_json(vega_url)

    # Format numeric columns and 'TQ' with commas
    numeric_cols = [col for col in source_df.columns if col.isdigit()] + ['TQ']
    source_df[numeric_cols] = source_df[numeric_cols].apply(lambda col: col.map(lambda x: f"{x:,}" if pd.notnull(x) else x))

    try:
        pd.testing.assert_frame_equal(source_df, vega_df)
        print("The DataFrames are identical.")
    except AssertionError as e:
        print("The DataFrames are not identical. Differences:", e)

if __name__ == "__main__":
    validate_budget_data()