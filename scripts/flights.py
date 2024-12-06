# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "pyarrow>=14.0.0",
# ]
# ///
"""
Process U.S. DOT On-Time Flight Performance data into a simplified CSV/JSON/Parquet format.

This script processes user-downloaded ZIP files containing Bureau of Transportation 
Statistics (BTS) On-Time Flight Performance data, combining and transforming them 
into a specified output format with essential flight delay information. The script 
properly handles date boundary cases where flights depart on a different date than 
scheduled due to delays or early departures. BTS is a statistical agency within 
the U.S. Department of Transportation (DOT).

Data Source: 
1) Visit https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr 
         (link valid as of November 2024)
2) Download prezipped files, one per month.

Input Data Requirements:
    - ZIP files containing BTS On-Time Performance data CSVs
    - Required columns in CSVs:
        * FlightDate: Scheduled departure date (YYYY-MM-DD)
        * CRSDepTime: Scheduled departure time (HHMM, 24-hour format)
        * DepTime: Actual departure time (HHMM, 24-hour format)
        * DepDelay: Departure delay in minutes
        * ArrDelay: Arrival delay in minutes
        * Distance: Flight distance in miles
        * Origin: Origin airport code
        * Dest: Destination airport code
        * Cancelled: Boolean indicating if flight was cancelled
Usage:
    ./flights.py INPUT_DIR [-o OUTPUT] [-n NUM_ROWS] [-s SEED] 
                          [-d DATETIME_FORMAT] [-f OUTPUT_FORMAT] [-c COLUMNS]
                          [-v] [--flag-date-changes] [--start-date START_DATE]
                          [--end-date END_DATE]

Arguments:
    INPUT_DIR           Directory containing flight data zip files (required)
    -o, --output        Output filename without extension (default: flights)
    -n, --num-rows      Number of rows to include in output (optional, defaults to all rows)
    -s, --seed          Random seed for row sampling (optional, defaults to 42)
    -d, --datetime-format DateTime format: 'mmddhhmm', 'iso', or 'decimal' (optional, defaults to 'mmddhhmm')
    -f, --format        Output format: 'csv', 'json', or 'parquet' (optional, defaults to 'csv')
    -c, --columns       Comma-separated list of columns to include in output and their order
                         If not specified, defaults to: date/time (datetime-format dependent),
                         delay, distance, origin, destination.
    -v, --verbose       Show detailed statistics about the dataset
    --flag-date-changes Add column indicating when actual departure date differs from scheduled
    --start-date        Start date (inclusive) in YYYY-MM-DD format to filter actual departures
    --end-date          End date (inclusive) in YYYY-MM-DD format to filter actual departures

    Parquet-specific options:
        --parquet-compression      Compression codec for Parquet files: 'zstd', 'snappy', 'gzip', 
                                or 'none' (default: zstd)
        --parquet-compression-level  Compression level for ZSTD (1-22, default: 3)
                                    Higher values give better compression but slower speed
        --parquet-row-group-size    Row group size in MB (default: 128)
                                    Larger values improve compression but use more memory
        --parquet-disable-dictionary Disable dictionary encoding for string columns
                                    Dictionary encoding improves compression for repeated values
        --parquet-dictionary-page-size  Dictionary page size in KB (default: 1024)
                                    Larger values may improve compression for string columns
        --parquet-disable-statistics    Disable writing statistics to Parquet file
                                    Statistics help with query planning but increase file size 


Available Columns:
    time                Decimal hours.minutes when using decimal format (e.g., 6.5 for 6:30)
    date                Formatted datetime when using mmddhhmm or iso format
    delay               Arrival delay in minutes (integer)
    distance            Flight distance in miles (integer)
    origin             Origin airport code
    destination        Destination airport code
    date_changed       Boolean indicating if actual departure date differs from scheduled
                       (only available with --flag-date-changes)
    ScheduledFlightDate Original scheduled flight date (YYYY-MM-DD)
    ScheduledFlightTime Original scheduled departure time (HHMM)
    DepDelay           Departure delay in minutes (integer)

Output Formats:
    datetime formats:
        - mmddhhmm: "06142330" (June 14, 23:30)
        - iso: "2023/06/14 23:30"
        - decimal: "6.5" (6:30), "6.25" (6:15), "23.75" (23:45)

    Output Format Details:
    - CSV:     Human-readable comma-separated values
    - JSON:    Compact JSON array of records, useful for APIs
    - Parquet: Columnar storage with compression, ideal for large datasets
              Supports ZSTD, SNAPPY, or GZIP compression

Examples:
    # Basic usage - process all rows, output as CSV with default columns
    python flights.py ./flight_data

    # Process 1000 rows with specific columns in decimal time format
    python flights.py ./flight_data -n 1000 -d decimal -c time,delay,distance

    # Output as JSON with ISO dates and scheduled information
    python flights.py ./flight_data -f json -d iso -c ScheduledFlightDate,ScheduledFlightTime,date,delay

    # Include date change flag and custom column selection
    python flights.py ./flight_data --flag-date-changes -c date,delay,date_changed,DepDelay

    # Filter flights between specific dates
    python flights.py ./flight_data --start-date 2023-01-01 --end-date 2023-01-31

    # Output as Parquet with custom compression settings
    python flights.py ./flight_data -f parquet --parquet-compression zstd --parquet-compression-level 7


Notes:
    - Input ZIP files should match the pattern 'On_Time_Reporting*.zip'
    - Files are expected to use ISO-8859-1 encoding
    - The script automatically handles date changes due to delays
    - Invalid or problematic rows are logged but excluded from the output
    - Column names are case-sensitive
    - When using decimal format, 'time' must be used instead of 'date'
    - When using mmddhhmm or iso format, 'date' must be used instead of 'time'
"""

import pandas as pd
import zipfile
import glob
import json
from typing import List, Optional, Union, Literal, Dict, Any, Set
import logging
from pathlib import Path
import argparse
import numpy as np
from enum import Enum
import pyarrow as pa
if pa.__version__ < '14.0.0':
    logging.warning(f"Using pyarrow version {pa.__version__}. Some Parquet features may not be available. Consider upgrading to 14.0.0 or later.")
import pyarrow.parquet as pq
from dataclasses import dataclass
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CompressionCodec(str, Enum):
    ZSTD = 'zstd'
    SNAPPY = 'snappy'
    GZIP = 'gzip'
    NONE = 'none'

class DateTimeFormat(str, Enum):
    MMDDHHMM = 'mmddhhmm'
    ISO = 'iso'
    DECIMAL = 'decimal'

class OutputFormat(str, Enum):
    CSV = 'csv'
    JSON = 'json'
    PARQUET = 'parquet'

@dataclass
class ParquetConfig:
    compression: str = 'zstd'
    compression_level: int = 3
    row_group_size: int = 128 * 1024 * 1024  # 128MB default
    enable_dictionary: bool = True
    dictionary_page_size: int = 1024 * 1024  # 1MB default
    write_statistics: bool = True
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'ParquetConfig':
        """Create ParquetConfig from command line arguments."""
        return cls(
            compression=args.parquet_compression,
            compression_level=args.parquet_compression_level,
            row_group_size=args.parquet_row_group_size * 1024 * 1024,
            enable_dictionary=not args.parquet_disable_dictionary,
            dictionary_page_size=args.parquet_dictionary_page_size * 1024,
            write_statistics=not args.parquet_disable_statistics
        )

# Define valid columns and their dependencies
VALID_COLUMNS = {
    'time', 'date', 'delay', 'distance', 'origin', 'destination',
    'date_changed', 'ScheduledFlightDate', 'ScheduledFlightTime', 'DepDelay'
}

# Columns that require the --flag-date-changes option
FLAG_DEPENDENT_COLUMNS = {'date_changed'}

# Columns that are format-dependent
FORMAT_DEPENDENT_COLUMNS = {
    DateTimeFormat.DECIMAL: {'time'},  # must use 'time' with decimal format
    DateTimeFormat.ISO: {'date'},      # must use 'date' with iso format
    DateTimeFormat.MMDDHHMM: {'date'}  # must use 'date' with mmddhhmm format
}

# Helper functions
def convert_hhmm_to_minutes(time_hhmm: float) -> Optional[int]:
    """Convert HHMM format to minutes since midnight."""
    if pd.isnull(time_hhmm):
        return None
    time_hhmm = int(time_hhmm)
    if time_hhmm == 2400:  # Handle special case
        return 0
    hours = time_hhmm // 100
    minutes = time_hhmm % 100
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes

def convert_to_decimal_time(dt: pd.Timestamp) -> float:
    """Convert datetime to decimal time format (e.g., 6:30 -> 6.5)."""
    return dt.hour + (dt.minute / 60)

def validate_columns(
    columns: List[str],
    datetime_format: DateTimeFormat,
    flag_date_changes: bool
) -> None:
    """Validate requested columns against format and flags."""
    column_set = set(columns)
    
    # Check all columns are valid
    invalid_columns = column_set - VALID_COLUMNS
    if invalid_columns:
        raise ValueError(f"Invalid columns: {', '.join(invalid_columns)}")
    
    # Check flag-dependent columns
    if not flag_date_changes and (column_set & FLAG_DEPENDENT_COLUMNS):
        raise ValueError("date_changed column requires --flag-date-changes option")
    
    # Check format-dependent columns
    if datetime_format == DateTimeFormat.DECIMAL:
        if 'date' in column_set:
            raise ValueError("Use 'time' instead of 'date' with decimal format")
    else:
        if 'time' in column_set:
            raise ValueError(f"Use 'date' instead of 'time' with {datetime_format.value} format")

def format_datetime(
    df: pd.DataFrame,
    datetime_format: DateTimeFormat
) -> pd.DataFrame:
    """Format datetime column according to specified format."""
    df = df.copy()
    
    if datetime_format == DateTimeFormat.DECIMAL:
        df['time'] = df['date'].apply(convert_to_decimal_time)
        df = df.drop('date', axis=1)
    elif datetime_format == DateTimeFormat.MMDDHHMM:
        df['date'] = df['date'].dt.strftime('%m%d%H%M')
    else:  # ISO format
        df['date'] = df['date'].dt.strftime('%Y/%m/%d %H:%M')
    
    return df

def process_flights_data(
   df: pd.DataFrame,
   num_rows: Optional[int] = None,
   random_seed: int = 42,
   datetime_convert: bool = True,
   datetime_format: DateTimeFormat = DateTimeFormat.MMDDHHMM,
   flag_date_changes: bool = False,
   columns: Optional[List[str]] = None,
   start_date: Optional[str] = None,
   end_date: Optional[str] = None
) -> pd.DataFrame:
   """Process flight data with specified columns and format."""
   # Set random seed for reproducibility
   np.random.seed(random_seed)
   
   # Filter cancelled flights and drop NA values first
   df = df[~df.Cancelled].dropna(subset=['ArrDelay', 'DepDelay', 'CRSDepTime'])

   # Add MMDDHHMM format check
   if datetime_format == DateTimeFormat.MMDDHHMM:
       unique_years = pd.to_datetime(df['FlightDate']).dt.year.unique()
       if len(unique_years) > 1:
           raise ValueError(
               f"MMDDHHMM format cannot be used with data spanning multiple years. "
               f"Found data from years: {sorted(unique_years)}. "
               "Please use ISO format (-d iso) for multi-year data."
           )

   # Calculate scheduled minutes and actual minutes for validation
   scheduled_minutes = (df['CRSDepTime'].astype(int) // 100 * 60 + 
                       df['CRSDepTime'].astype(int) % 100)
   actual_minutes = scheduled_minutes + df['DepDelay'].astype(int)

   # Vectorized validation
   dep_time_minutes = (df['DepTime'] // 100 * 60 + df['DepTime'] % 100).where(df['DepTime'] != 2400, 0)
   
   # Handle midnight crossing
   time_diff = np.abs(dep_time_minutes - actual_minutes % 1440)
   time_diff = np.minimum(time_diff, 1440 - time_diff)
   
   # Check consistency with 1-minute tolerance
   all_consistent = (~pd.isnull(df['DepTime'])) & (time_diff <= 1)
   
   logging.info(
       "All reported departure times are consistent with delays"
       if all_consistent.all()
       else "Some reported departure times are inconsistent with delays"
   )
   
   # Calculate actual datetime
   flight_dates = pd.to_datetime(df['FlightDate'])
   df['actual_datetime'] = (flight_dates + 
                          pd.to_timedelta(scheduled_minutes, unit='m') + 
                          pd.to_timedelta(df['DepDelay'], unit='m'))
   
   # Special handling for 2400 DepTime (midnight next day)
   mask_2400 = df['DepTime'] == 2400
   if mask_2400.any():
       df.loc[mask_2400, 'actual_datetime'] = flight_dates[mask_2400] + pd.Timedelta(days=1)

   # Store scheduled dates before filtering
   df['scheduled_date'] = flight_dates.dt.date

   # Filter by date range if specified
   if start_date or end_date:
       if start_date:
           start_dt = pd.to_datetime(start_date)
           df = df[df['actual_datetime'].dt.date >= start_dt.date()]
       if end_date:
           end_dt = pd.to_datetime(end_date)
           df = df[df['actual_datetime'].dt.date <= end_dt.date()]
       
       if len(df) == 0:
           logging.warning(f"No flights found within specified date range")
       else:
           logging.info(f"Found {len(df)} flights within specified date range")

   # Calculate date changes if requested
   if flag_date_changes:
       df['date_changed'] = df['scheduled_date'] != df['actual_datetime'].dt.date
       df = df.drop('scheduled_date', axis=1)  # Clean up temporary column

   # Create result DataFrame with all possible columns
   result = pd.DataFrame({
       'date': df['actual_datetime'],
       'delay': df['ArrDelay'].astype(int),
       'distance': df['Distance'].astype(int),
       'origin': df['Origin'],
       'destination': df['Dest'],
       'ScheduledFlightDate': df['FlightDate'],
       'ScheduledFlightTime': df['CRSDepTime'],
       'DepDelay': df['DepDelay'].astype(int)
   })
   
   if flag_date_changes:
       result['date_changed'] = df['date_changed']
   
   # Format datetime according to specified format
   if datetime_convert:
       result = format_datetime(result, datetime_format)
   
   # Handle sampling if requested
   if num_rows is not None and num_rows < len(result):
       result = result.sample(n=num_rows, random_state=random_seed)
       result = result.sort_values('time' if datetime_format == DateTimeFormat.DECIMAL else 'date')
       logging.info(f"Randomly sampled {num_rows} rows from {len(df)} total rows")
   
   # Select and order columns if specified
   if columns:
       validate_columns(columns, datetime_format, flag_date_changes)
       result = result[columns]
   else:
       default_cols = ['time' if datetime_format == DateTimeFormat.DECIMAL else 'date',
                      'delay', 'distance', 'origin', 'destination']
       result = result[default_cols]
   
   return result

def get_dataset_stats(df: pd.DataFrame, datetime_format: DateTimeFormat) -> Dict[str, Any]:
    """Calculate and return detailed statistics about the dataset."""
    time_col = 'time' if datetime_format == DateTimeFormat.DECIMAL else 'date'
    
    if datetime_format == DateTimeFormat.DECIMAL:
        stats = {
            'time_range': {
                'min': f"{df[time_col].min():.4f}",
                'max': f"{df[time_col].max():.4f}"
            }
        }
    elif datetime_format == DateTimeFormat.MMDDHHMM:
        stats = {
            'date_range': {
                'min': df[time_col].min(),
                'max': df[time_col].max()
            }
        }
    else:  # ISO format
        stats = {
            'date_range': {
                'min': df[time_col].min(),
                'max': df[time_col].max()
            }
        }
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    stats.update({
        col + '_stats': {
            'min': int(df[col].min()) if col in ['delay', 'distance', 'DepDelay'] else df[col].min(),
            'max': int(df[col].max()) if col in ['delay', 'distance', 'DepDelay'] else df[col].max(),
            'mean': round(df[col].mean(), 2) if col in ['delay', 'distance', 'DepDelay'] else None
        } for col in numeric_columns if col != time_col
    })
    
    if 'origin' in df.columns or 'destination' in df.columns:
        stats['airports'] = {
            'origins': sorted(df['origin'].unique().tolist()) if 'origin' in df.columns else [],
            'destinations': sorted(df['destination'].unique().tolist()) if 'destination' in df.columns else [],
            'total_origins': len(df['origin'].unique()) if 'origin' in df.columns else 0,
            'total_destinations': len(df['destination'].unique()) if 'destination' in df.columns else 0
        }
    
    return stats

def print_verbose_stats(stats: Dict[str, Any]) -> None:
    """Print detailed statistics in a formatted way."""
    logging.info("\nDataset Statistics:")
    logging.info("===================")
    
    if 'time_range' in stats:
        logging.info("\nTime Range:")
        logging.info(f"  From: {stats['time_range']['min']}")
        logging.info(f"  To:   {stats['time_range']['max']}")
    elif 'date_range' in stats:
        logging.info("\nDate Range:")
        logging.info(f"  From: {stats['date_range']['min']}")
        logging.info(f"  To:   {stats['date_range']['max']}")
    
    for stat_name, stat_values in stats.items():
        if stat_name.endswith('_stats'):
            col_name = stat_name.replace('_stats', '')
            logging.info(f"\n{col_name.title()} Statistics:")
            if 'min' in stat_values:
                logging.info(f"  Minimum: {stat_values['min']}")
            if 'max' in stat_values:
                logging.info(f"  Maximum: {stat_values['max']}")
            if 'mean' in stat_values and stat_values['mean'] is not None:
                logging.info(f"  Mean:    {stat_values['mean']}")
    
    if 'airports' in stats:
        logging.info("\nAirports:")
        if stats['airports']['total_origins']:
            logging.info(f"  Total Origin Airports:      {stats['airports']['total_origins']}")
            logging.info("\nOrigin Airports:")
            logging.info(f"  {', '.join(stats['airports']['origins'])}")
        if stats['airports']['total_destinations']:
            logging.info(f"  Total Destination Airports: {stats['airports']['total_destinations']}")
            logging.info("\nDestination Airports:")
            logging.info(f"  {', '.join(stats['airports']['destinations'])}")
    logging.info("\n")

def add_parquet_arguments(parser: argparse.ArgumentParser) -> None:
    """Add Parquet-specific arguments to the parser."""
    parquet_group = parser.add_argument_group('Parquet options')
    parquet_group.add_argument(
        '--parquet-compression',
        choices=[codec.value for codec in CompressionCodec],
        default='zstd',
        help='Compression codec for Parquet output (default: %(default)s)'
    )
    parquet_group.add_argument(
        '--parquet-compression-level',
        type=int,
        default=3,
        choices=range(1, 23),
        help='Compression level for ZSTD (1-22, default: %(default)s)'
    )
    parquet_group.add_argument(
        '--parquet-row-group-size',
        type=int,
        default=128,
        help='Row group size in MB (default: %(default)s)'
    )
    parquet_group.add_argument(
        '--parquet-disable-dictionary',
        action='store_true',
        help='Disable dictionary encoding'
    )
    parquet_group.add_argument(
        '--parquet-dictionary-page-size',
        type=int,
        default=1024,
        help='Dictionary page size in KB (default: %(default)s)'
    )
    parquet_group.add_argument(
        '--parquet-disable-statistics',
        action='store_true',
        help='Disable writing statistics to Parquet file'
    )

def parse_args() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description='''
Process BTS On-Time Flight Performance data into a simplified CSV/JSON/Parquet format.

This script processes ZIP files containing Bureau of Transportation Statistics (BTS)
On-Time Flight Performance data, combining and transforming them into a specified
output format with essential flight delay information.

Data Source (valid as of November 2024):
    1. Visit https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr
    2. Select "Prezipped File" option
    3. Download one zip file per month into your input directory
    4. Each file should follow the pattern 'On_Time_Reporting*.zip'
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    # Basic usage - process all rows, output as CSV with default columns
    %(prog)s ./flight_data

    # Process 1000 rows with specific columns in decimal time format
    %(prog)s ./flight_data -n 1000 -d decimal -c time,delay,distance

    # Output as JSON with ISO dates and scheduled information
    %(prog)s ./flight_data -f json -d iso -c ScheduledFlightDate,ScheduledFlightTime,date,delay

    # Include date change flag and custom column selection
    %(prog)s ./flight_data --flag-date-changes -c date,delay,date_changed,DepDelay

Notes:
    - Input ZIP files should match the pattern 'On_Time_Reporting*.zip'
    - Files are expected to use ISO-8859-1 encoding
    - The script automatically handles date changes due to delays
    - Invalid rows are logged but excluded from the output
    - Column names are case-sensitive
    - Source data URL and format may change after November 2024
    ''')

    add_parquet_arguments(parser)

    parser.add_argument('input_dir', 
                       help='Directory containing flight data zip files downloaded from BTS')
    
    parser.add_argument('-o', '--output', 
                       default='flights',
                       help='Output filename without extension (default: %(default)s)')
    
    parser.add_argument('-n', '--num-rows', 
                       type=int,
                       metavar='N',
                       help='Number of rows to include in output (default: all rows)')
    
    parser.add_argument('-s', '--seed', 
                       type=int, 
                       default=42,
                       help='Random seed for row sampling (default: %(default)s)')

    parser.add_argument('--start-date',
                   type=str,
                   help='Start date (inclusive) in YYYY-MM-DD format to filter actual departures')
    parser.add_argument('--end-date',
                   type=str,
                   help='End date (inclusive) in YYYY-MM-DD format to filter actual departures')
    
    datetime_help = '''
    DateTime format for output (default: %(default)s)
    
    Available formats:
      mmddhhmm: "06142330" (June 14, 23:30)
      iso:      "2023/06/14 23:30"
      decimal:  "6.5" (6:30), "23.75" (23:45)
    
    Note: Use 'time' column with decimal format, 'date' with others
    '''
    parser.add_argument('-d', '--datetime-format',
                       type=str,
                       choices=[format.value for format in DateTimeFormat],
                       default=DateTimeFormat.MMDDHHMM.value,
                       help=datetime_help)
    
    parser.add_argument('-f', '--format',
                       type=str,
                       choices=[format.value for format in OutputFormat],
                       default=OutputFormat.CSV.value,
                       help='Output format: csv, json, or parquet (default: %(default)s)')
  
    columns_help = '''
    Comma-separated list of columns to include and their order. Available columns:
    time, date, delay, distance, DepDelay, origin, destination, ScheduledFlightDate, ScheduledFlightTime, date_changed
    [Note: time may be selected only with decimal format.] Default is date,delay,distance,origin,destination.

    Example: -c date,delay,distance,origin,destination
    '''
    parser.add_argument('-c', '--columns',
                       type=str,
                       metavar='COLS',
                       help=columns_help)
    
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Show detailed statistics about the dataset')
    
    parser.add_argument('--flag-date-changes',
                       action='store_true',
                       help='Add column indicating when actual departure date differs from scheduled')
    
    return parser.parse_args()

# I/O functions

def load_zip_files(pattern: str) -> pd.DataFrame:
    """Load and combine CSV files from matching zip files."""
    zip_files = glob.glob(pattern)
    if not zip_files:
        raise FileNotFoundError(f"No zip files found matching pattern: {pattern}")
    
    dfs: List[pd.DataFrame] = []
    needed_cols = ['FlightDate', 'CRSDepTime', 'DepTime', 'DepDelay', 'ArrDelay', 'Distance', 
                  'Origin', 'Dest', 'Cancelled']

    for zip_file in zip_files:
        logging.info(f"Processing {zip_file}")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            for csv_file in csv_files:
                with zip_ref.open(csv_file) as f:
                    df = pd.read_csv(f, 
                                   encoding='iso-8859-1',
                                   usecols=needed_cols,
                                   dtype={'Cancelled': 'bool'})
                    dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)


def save_as_parquet(df: pd.DataFrame, filename: str, config: ParquetConfig) -> None:
    """Save DataFrame as Parquet file with specified configuration."""
    is_zstd = config.compression == "zstd"
    kwds = {"compression_level": config.compression_level} if is_zstd else {}
    df.to_parquet(
        filename,
        compression=config.compression,
        index=False,
        use_dictionary=config.enable_dictionary,
        write_statistics=config.write_statistics,
        **kwds,
    )

    # Get and log file statistics
    file_stats = os.stat(filename)
    level = f" (level {config.compression_level})" if is_zstd else ""
    msg = (
        f"Parquet file statistics:\n"
        f"  - File size: {file_stats.st_size / (1024*1024):.2f} MB\n"
        f"  - Number of row groups: {pq.ParquetFile(filename).num_row_groups}\n"
        f"  - Compression: {config.compression}{level}\n"
        f"  - Row group size: {config.row_group_size / (1024*1024):.0f} MB"
    )
    logging.info(msg)

def save_output(
    df: pd.DataFrame,
    output_format: OutputFormat,
    base_filename: str,
    datetime_format: DateTimeFormat,
    parquet_config: ParquetConfig,
    verbose: bool = False,
) -> None:
    """Save the DataFrame in the specified format and optionally show statistics."""
    if verbose:
        stats = get_dataset_stats(df, datetime_format)
        print_verbose_stats(stats)
    output_filename = f"{base_filename}.{output_format.value}"
    if output_format == OutputFormat.CSV:
        df.to_csv(output_filename, index=False)
    elif output_format == OutputFormat.JSON:
        s = json.dumps(df.to_dict(orient="records"), separators=(",", ":"))
        Path(output_filename).write_text(s, encoding="utf-8")
    else:  # PARQUET
        save_as_parquet(df, output_filename, parquet_config)

    logging.info(f"Successfully created {output_filename} with {len(df)} rows")

def main():
    args = parse_args()
    is_parquet = args.format == 'parquet'
    parquet_config = ParquetConfig.from_args(args) if is_parquet else ParquetConfig()
    base_filename = args.output
    zip_pattern = str(Path(args.input_dir) / '*On_Time_Reporting*.zip')
    
    try:
        # Parse columns if provided
        columns = args.columns.split(',') if args.columns else None
        
        raw_df = load_zip_files(zip_pattern)
        datetime_format = DateTimeFormat(args.datetime_format)
        processed_df = process_flights_data(
            raw_df,
            num_rows=args.num_rows,
            random_seed=args.seed,
            datetime_convert=not is_parquet,
            datetime_format=datetime_format,
            flag_date_changes=args.flag_date_changes,
            columns=columns,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        save_output(
            processed_df,
            output_format=OutputFormat(args.format),
            base_filename=base_filename,
            datetime_format=datetime_format,
            verbose=args.verbose,
            parquet_config=parquet_config
        )
        
    except Exception as e:
        logging.error(f"Error processing flight data: {str(e)}")
        if isinstance(e, ValueError) and "column" in str(e).lower():
            # Provide more helpful error message for column-related errors
            logging.error("\nValid columns are:")
            logging.error(f"- When using decimal format: {', '.join(sorted(VALID_COLUMNS - {'date'}))}")
            logging.error(f"- When using other formats: {', '.join(sorted(VALID_COLUMNS - {'time'}))}")
            logging.error("\nNote: 'date_changed' requires --flag-date-changes option")
        raise

if __name__ == '__main__':
    main()