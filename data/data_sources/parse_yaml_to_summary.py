import yaml
import pandas as pd
from pathlib import Path
import glob
import re


def parse_yaml_file(yaml_file_path):
    """
    Parse a single YAML file and return DataFrame with results
    """
    # Check if file exists
    if not Path(yaml_file_path).exists():
        raise FileNotFoundError(f'YAML file not found: {yaml_file_path}')

    # Check if file is empty
    if Path(yaml_file_path).stat().st_size == 0:
        raise ValueError(f'YAML file is empty: {yaml_file_path}')

    # Read the raw YAML file content to preserve comments
    with open(yaml_file_path, 'r') as file:
        raw_content = file.read()

    # Parse YAML structure (without comments)
    data = yaml.safe_load(raw_content)

    # Check if YAML was parsed correctly
    if data is None:
        raise ValueError(
            f'YAML file is empty or contains only comments: {yaml_file_path}')

    # Now parse the raw content to extract comments associated with datafiles
    results = []
    file_name = Path(yaml_file_path).stem  # Get filename without extension

    # Parse the raw YAML content line by line to find datafiles with comments
    lines = raw_content.split('\n')
    current_key = None
    in_datafiles_block = False
    datafile_comments = {}  # Store comments for each datafile
    current_indent = 0

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue

        # Track indentation level
        indent_level = len(line) - len(line.lstrip())

        # Track current YAML key
        if stripped_line.endswith(':'):
            current_key = stripped_line[:-1].strip()
            in_datafiles_block = (current_key == 'datafiles')
            current_indent = indent_level
            continue

        # Check if we're still in the same block (same or greater indentation)
        if indent_level <= current_indent:
            in_datafiles_block = False

        # Check if we're in a datafiles block and it's a datafile entry
        if in_datafiles_block and stripped_line.startswith('- '):
            # Extract datafile URL and comment
            match = re.match(
                r'-\s+(https?://[^\s#]+)(?:\s*#\s*(.+))?', stripped_line)
            if match:
                datafile_url = match.group(1).strip()
                comment = match.group(2).strip() if match.group(2) else None
                datafile_comments[datafile_url] = comment

    # Now process the parsed YAML data
    for key, config in data.items():
        # Skip if config is not a dictionary (could be comments or malformed data)
        if not isinstance(config, dict):
            print(
                f"Warning: Skipping '{key}' in {yaml_file_path} - not a valid configuration dictionary")
            continue

        # Get collection name and handle empty/missing values
        collection_name = config.get('collection', '')
        if isinstance(collection_name, str):
            collection_name = collection_name.strip()
        if not collection_name:
            print(
                f"Warning: Skipping '{key}' in {yaml_file_path} - empty or missing collection name")
            continue

        # Extract adapter name from command
        command = config.get('command', '')
        adapter_name = None

        # Parse adapter name from command
        if command and '--adapter' in command:
            parts = command.split()
            for i, part in enumerate(parts):
                if part == '--adapter' and i + 1 < len(parts):
                    adapter_name = parts[i + 1]
                    break

        # Handle datafiles - check if the key exists
        if 'datafiles' not in config:
            print(
                f"Warning: Skipping '{key}' in {yaml_file_path} - missing 'datafiles' key")
            continue

        datafiles = config['datafiles']
        if isinstance(datafiles, str):
            datafiles = [datafiles]
        elif not isinstance(datafiles, list):
            print(
                f"Warning: Skipping '{key}' in {yaml_file_path} - datafiles is not a list or string")
            continue

        # Extract additional fields
        other_fields = ['source', 'label', 'biological_process', 'method', 'type',
                        'source_annotation', 'molecular_function', 'version', 'threshold', 'relationship']

        # Create a row for each datafile
        for datafile in datafiles:
            # Ensure datafile is a string before processing
            if not isinstance(datafile, str):
                print(
                    f"Warning: Skipping non-string datafile in '{key}': {datafile}")
                continue

            # Get the comment from our manually parsed datafile_comments dict
            notes = datafile_comments.get(datafile.strip(), None)

            # Create result dictionary with all fields
            result_entry = {
                'source_file': file_name,
                'yaml_entry_name': key,
                'collection': collection_name,
                'adapter_name': adapter_name,
                'datafile': datafile,
                'notes': notes
            }
            for field in other_fields:
                result_entry.update({field: config.get(field, None)})

            results.append(result_entry)

    return pd.DataFrame(results)


def parse_multiple_yaml_files(yaml_files, output_dir='output', single_excel_file='collections_summary.xlsx'):
    """
    Parse multiple YAML files and create Excel outputs
    """
    all_results = []

    for yaml_file in yaml_files:
        try:
            print(f'Processing: {yaml_file}')
            df = parse_yaml_file(yaml_file)
            if not df.empty:
                all_results.append(df)
                print(f'  Found {len(df)} entries')
            else:
                print(f'  No valid entries found')
        except Exception as e:
            print(f'Error processing {yaml_file}: {e}')

    # Combine all results
    if not all_results:
        print('No valid data found in any YAML files')
        return pd.DataFrame()

    combined_df = pd.concat(all_results, ignore_index=True)

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    # Define column order (core fields first, then additional fields)
    core_columns = ['source_file', 'collection',
                    'yaml_entry_name', 'adapter_name', 'datafile', 'notes']
    other_fields = ['source', 'label', 'biological_process', 'method', 'type',
                    'source_annotation', 'molecular_function', 'version', 'threshold', 'relationship']

    # Reorder columns
    column_order = core_columns + other_fields
    combined_df = combined_df[column_order]

    # Create individual Excel files for each collection
    for collection_name in combined_df['collection'].unique():
        collection_df = combined_df[combined_df['collection']
                                    == collection_name]

        # Clean filename and ensure it's not empty
        clean_name = collection_name.replace(' ', '_').replace(
            '/', '_').replace('\\', '_').strip()
        if not clean_name:
            print(f'Warning: Skipping collection with empty name')
            continue

        individual_filename = f'{output_dir}/{clean_name}.xlsx'

        # Save to individual Excel file
        collection_df.to_excel(individual_filename,
                               index=False, engine='openpyxl')
        print(f'Created individual Excel file: {individual_filename}')

    # Create single Excel file with multiple sheets
    with pd.ExcelWriter(single_excel_file, engine='openpyxl') as writer:
        # Create master sheet with all data
        try:
            combined_df.to_excel(
                writer, sheet_name='ALL_COLLECTIONS', index=False)
        except Exception as e:
            print(f'Warning: Could not create master sheet: {e}')

        # Create sheet for each collection
        for collection_name in combined_df['collection'].unique():
            collection_df = combined_df[combined_df['collection']
                                        == collection_name]

            # Clean sheet name and ensure it's not empty
            sheet_name = collection_name[:31].replace(
                ' ', '_').replace('/', '_').replace('\\', '_').strip()
            if not sheet_name:
                print(f'Warning: Skipping sheet with empty name')
                continue

            try:
                collection_df.to_excel(
                    writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                print(f"Warning: Could not create sheet '{sheet_name}': {e}")

    print(
        f'Created single Excel file with multiple sheets: {single_excel_file}')

    return combined_df


def main():
    # Define your YAML file patterns - modify these as needed
    yaml_patterns = [
        '*.yaml',                       # All YAML files in current directory
    ]

    # Collect all YAML files
    yaml_files = []
    for pattern in yaml_patterns:
        found_files = glob.glob(pattern)
        yaml_files.extend(found_files)

    # Remove duplicates and sort
    yaml_files = sorted(list(set(yaml_files)))

    if not yaml_files:
        print('No YAML files found. Please check your file patterns.')
        print('Current patterns:', yaml_patterns)
        return

    print(f'Found {len(yaml_files)} YAML file(s):')
    for file in yaml_files:
        print(f'  - {file}')

    try:
        # Parse and create both single and individual Excel files
        result_df = parse_multiple_yaml_files(
            yaml_files,
            output_dir='collections_individual',
            single_excel_file='collections_summary.xlsx'
        )

        if not result_df.empty:
            # Print summary
            print(f'\nSummary:')
            print(
                f"Total YAML files processed: {len(result_df['source_file'].unique())}")
            print(
                f"Total collections: {len(result_df['collection'].unique())}")
            print(
                f"Total YAML entries: {len(result_df['yaml_entry_name'].unique())}")
            print(f'Total datafiles: {len(result_df)}')
            print(f"Entries with notes: {result_df['notes'].notna().sum()}")
            print(
                f"Source files: {', '.join(result_df['source_file'].unique())}")
            print(
                f"Collections found: {', '.join(result_df['collection'].unique())}")
            print(f'\nFiles created:')
            print(f'- Single Excel with all sheets: collections_summary.xlsx')
            print(f'- Individual Excel files in: collections_individual/')
        else:
            print('No data was processed from any YAML files.')

    except Exception as e:
        print(f'Unexpected error: {e}')
        print('Please check your YAML file structures and ensure all required packages are installed.')


if __name__ == '__main__':
    main()
