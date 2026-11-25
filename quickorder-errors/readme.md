# QuickOrder and Zettle Data Processing Scripts

This repository contains scripts for processing CSV exports from QuickOrder and Zettle, filtering data based on specific criteria, and managing CSV files efficiently.

## Scripts Overview

1. **QuickOrder CSV Export Script**
   - **Purpose:** To download CSV exports from the QuickOrder API for each day within specified date ranges. This script uses multithreading to accelerate the downloading process.
   - **File:** `fetch_quickorder_purchases.py`

2. **Zettle CSV Export Script**
   - **Purpose:** To fetch purchase data from the Zettle API for each month within specified year ranges, and save it as CSV files. The script only creates CSV files when there is data available.
   - **File:** `fetch_zettle_purchases.py`

3. **CSV Concatenation and Filtering Script**
   - **Purpose:** To concatenate CSV files, filter them by matching certain data points, and produce a refined CSV output.
   - **File:** `get_quickorder_errors.py`

## Setup

### Environment Variables

Both QuickOrder and Zettle scripts require environment variables for authentication and configuration. Store these in a `.env` file at the root of the project:

```bash
QUICKORDER_USERNAME=<YourQuickOrderUsername>
QUICKORDER_PASSWORD=<YourQuickOrderPassword>
ZETTLE_ID=<YourZettleClientID>
ZETTLE_SECRET=<YourZettleSecret>
```

### Dependencies

Requires [uv](https://docs.astral.sh/uv/), which installs Python and the dependencies on `uv run`.

## Usage Instructions

### QuickOrder CSV Export Script

1. Run the script to fetch and save CSV files for each day:

```bash
uv run fetch_quickorder_purchases.py
```

2. The script will store CSV files in the `csv` folder. It automatically skips days for which files already exist.

### Zettle CSV Export Script

1. Run the script to fetch and save purchase data for each month:

```bash
uv run fetch_zettle_purchases.py
```

2. The script will store CSV files in the `zettle_csv` folder. It skips months with existing files.

### CSV Concatenation and Filtering Script

1. Edit the script to specify input folders and file patterns.

2. Run the script to concatenate and filter data:

```bash
uv run get_quickorder_errors.py
```

3. The script identifies records in Zettle data not present in QuickOrder based on specified columns, and saves the filtered data to `filtered_data.csv`.

## Notes

- Ensure the folders `csv` and `zettle_csv` exist or are created at runtime by the scripts.
- Review the log output produced by scripts, which provides detailed insights into the downloading, fetching, and data processing steps.
- For performance tuning, adjust the number of concurrent threads in the QuickOrder script's `ThreadPoolExecutor`.

