import pandas as pd
import glob
import os

def concatenate_csv_files(input_folder, output_file_pattern):
    # Find all CSV files in the input folder that match the export pattern
    csv_files = glob.glob(os.path.join(input_folder, output_file_pattern))
    print(f"Found {len(csv_files)} CSV files to concatenate in {input_folder}.")

    # List to hold DataFrames
    dataframes = []

    # Load each CSV file into a DataFrame and append to the list
    for file in csv_files:
        print(f"Loading data from {file}")
        df = pd.read_csv(file)
        dataframes.append(df)

    # Concatenate all DataFrames
    print("Concatenating data...")
    combined_df = pd.concat(dataframes, ignore_index=True)

    print("Concatenation done.")
    return combined_df

# Specify the folder containing CSV files and the output pattern
quickorder_input_folder = './csv'
zettle_input_folder = './zettle_csv'
quickorder_file_pattern = 'export_*.csv'  # Common pattern for file matching
zettle_file_pattern = 'purchases_*.csv'  # Common pattern for file matching

# Concatenate files
quickorder_data = concatenate_csv_files(quickorder_input_folder, quickorder_file_pattern)
zettle_data = concatenate_csv_files(zettle_input_folder, zettle_file_pattern)

# Assuming columns "products_0_name" is in `zettle_data` and "external reference" is in `quickorder_data`
beskrivelse_column = 'products_0_name'
external_reference_column = 'external reference'

# Perform the filtering operation
filtered_data = zettle_data[~zettle_data[beskrivelse_column].isin(quickorder_data[external_reference_column])]

# Print the filtered data
print(filtered_data)

# Optional: Save the filtered result to a new CSV file
filtered_data.to_csv('filtered_data.csv', index=False)
