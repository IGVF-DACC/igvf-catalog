import yaml
import pandas as pd
from pathlib import Path
import glob
import re


def extract_files_filesets_key(datafile_url):
    """
    Extract the files_filesets_key from a datafile URL.
    Example:
    https://api.data.igvf.org/reference-files/IGVFFI6699ZOCP/@@download/IGVFFI6699ZOCP.vcf.gz
    -> 'IGVFFI6699ZOCP'
    """
    if not isinstance(datafile_url, str):
        return None

    # Pattern to match the identifier in the URL
    patterns = [
        r'reference-files/([^/]+)/@@download',  # For reference-files pattern
        r'files/([^/]+)/@@download',           # For files pattern
        # Fallback: extract before file extension
        r'download/([^/]+)\.',
    ]

    for pattern in patterns:
        match = re.search(pattern, datafile_url)
        if match:
            return match.group(1)

    # If no pattern matches, return the original URL or None
    return None


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
    in_file_mappings_block = False
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
            in_file_mappings_block = (current_key == 'file_mappings')
            current_indent = indent_level
            continue

        # Check if we're still in the same block (same or greater indentation)
        if indent_level <= current_indent:
            in_datafiles_block = False
            in_file_mappings_block = False

        # Check if we're in a datafiles block and it's a datafile entry
        if in_datafiles_block and stripped_line.startswith('- '):
            # Extract datafile URL and comment
            match = re.match(
                r'-\s+(https?://[^\s#]+)(?:\s*#\s*(.+))?', stripped_line)
            if match:
                datafile_url = match.group(1).strip()
                comment = match.group(2).strip() if match.group(2) else None
                datafile_comments[datafile_url] = comment

        # Check if we're in a file_mappings block and it's a mapping entry
        if in_file_mappings_block and stripped_line.startswith('- '):
            # Extract datafile URL and comment from file_mappings
            match = re.match(
                r'-\s+datafile:\s+(https?://[^\s#]+)(?:\s*#\s*(.+))?', stripped_line)
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

        # Handle both datafiles and file_mappings structures
        datafiles_to_process = []

        # Check for traditional datafiles list
        if 'datafiles' in config:
            datafiles = config['datafiles']
            datafiles_to_process.extend(extract_nested_datafiles(datafiles))

        # Check for file_mappings structure
        if 'file_mappings' in config:
            file_mappings = config['file_mappings']
            if isinstance(file_mappings, list):
                for mapping in file_mappings:
                    if isinstance(mapping, dict) and 'datafile' in mapping:
                        datafiles_to_process.append(mapping)

        if not datafiles_to_process:
            print(
                f"Warning: Skipping '{key}' in {yaml_file_path} - no valid datafiles found")
            continue

        # Extract additional fields
        other_fields = ['source', 'label', 'biological_process', 'method', 'type',
                        'source_annotation', 'molecular_function', 'version', 'threshold', 'relationship']

        # Create a row for each datafile
        for datafile_info in datafiles_to_process:
            datafile = datafile_info.get('datafile')

            # Ensure datafile is a string before processing
            if not isinstance(datafile, str):
                print(
                    f"Warning: Skipping non-string datafile in '{key}': {datafile}")
                continue

            # Get the comment from our manually parsed datafile_comments dict
            notes = datafile_comments.get(datafile.strip(), None)

            # Extract files_filesets_key from datafile URL
            files_filesets_key = extract_files_filesets_key(datafile)

            # Create result dictionary with all fields
            result_entry = {
                'source_file': file_name,
                'yaml_entry_name': key,
                'collection': collection_name,
                'adapter_name': adapter_name,
                'datafile': datafile,
                'files_filesets_key': files_filesets_key,  # Add extracted key
                'notes': notes,
                '_key': datafile  # Keep original _key for backward compatibility
            }

            # Add all other fields from config
            for field in other_fields:
                result_entry.update({field: config.get(field, None)})

            # Add reference_filepath if it exists in the mapping
            if 'reference_filepath' in datafile_info:
                result_entry['reference_filepath'] = datafile_info['reference_filepath']
            else:
                result_entry['reference_filepath'] = None

            # Add nested context information if available
            if 'nested_context' in datafile_info:
                result_entry['nested_context'] = datafile_info['nested_context']
            else:
                result_entry['nested_context'] = None

            results.append(result_entry)

    return pd.DataFrame(results)


def extract_nested_datafiles(datafiles_structure, current_context=None):
    """
    Recursively extract datafiles from nested YAML structure.
    Handles structures like:
    - AFR:
      - chr1:
        - https://url1
        - https://url2
      - chr2:
        - https://url3
    """
    datafiles_list = []

    if current_context is None:
        current_context = []

    if isinstance(datafiles_structure, list):
        for item in datafiles_structure:
            if isinstance(item, str):
                # Found a URL string
                datafiles_list.append({
                    'datafile': item,
                    'nested_context': ' > '.join(current_context) if current_context else None
                })
            elif isinstance(item, dict):
                # Found a nested dictionary, recurse into it
                datafiles_list.extend(
                    extract_nested_datafiles(item, current_context))
            else:
                print(
                    f'Warning: Unexpected data type in datafiles list: {type(item)}')

    elif isinstance(datafiles_structure, dict):
        for key, value in datafiles_structure.items():
            if isinstance(value, (list, dict)):
                # Add current key to context and recurse
                new_context = current_context + [str(key)]
                datafiles_list.extend(
                    extract_nested_datafiles(value, new_context))
            else:
                print(
                    f'Warning: Unexpected value type in datafiles dict: {type(value)}')

    return datafiles_list


def load_tsv_file(tsv_file_path):
    """
    Load the TSV file and return as DataFrame
    """
    if not Path(tsv_file_path).exists():
        raise FileNotFoundError(f'TSV file not found: {tsv_file_path}')

    print(f'Loading TSV file: {tsv_file_path}')
    tsv_df = pd.read_csv(tsv_file_path, sep='\t')
    print(f'  Loaded {len(tsv_df)} rows from TSV file')
    print(f'  TSV columns: {list(tsv_df.columns)}')

    return tsv_df


def merge_with_tsv(yaml_df, tsv_df, merge_key='files_filesets_key'):
    """
    Merge YAML DataFrame with TSV DataFrame using the specified key
    """
    if merge_key not in yaml_df.columns:
        raise ValueError(
            f'Merge key "{merge_key}" not found in YAML DataFrame')

    if merge_key not in tsv_df.columns:
        print(
            f'Warning: Merge key "{merge_key}" not found in TSV DataFrame. Available columns: {list(tsv_df.columns)}')
        print('Falling back to _key column for merging')
        if '_key' in tsv_df.columns:
            merge_key = '_key'
        else:
            raise ValueError(f'No suitable merge key found in TSV DataFrame')

    print(f'Merging DataFrames using key: {merge_key}')
    print(f'  YAML DataFrame shape: {yaml_df.shape}')
    print(f'  TSV DataFrame shape: {tsv_df.shape}')

    # Check how many keys in YAML have matches in TSV
    yaml_keys = set(yaml_df[merge_key].dropna())
    tsv_keys = set(tsv_df[merge_key].dropna())
    matching_keys = yaml_keys.intersection(tsv_keys)

    print(f'  Matching keys found: {len(matching_keys)}/{len(yaml_keys)}')

    # Merge using left join to keep all YAML entries
    merged_df = pd.merge(yaml_df, tsv_df, on=merge_key,
                         how='left', suffixes=('', '_tsv'))

    print(f'  Merged DataFrame shape: {merged_df.shape}')
    print(f'  Successful merges: {merged_df[merge_key].notna().sum()}')

    return merged_df


def drop_empty_columns(df):
    """
    Drop columns that have only empty strings
    """
    columns_to_drop = []
    for column in df.columns:
        if (df[column].astype(str).str.strip() == '').all():
            columns_to_drop.append(column)

    if columns_to_drop:
        print(f'  Dropping empty columns: {columns_to_drop}')
        df = df.drop(columns=columns_to_drop)

    return df


def parse_multiple_yaml_files(yaml_files, tsv_file_path, single_excel_file='collections_summary.xlsx'):
    """
    Parse multiple YAML files, merge with TSV, and create Excel outputs
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

    # Load and merge with TSV file
    try:
        tsv_df = load_tsv_file(tsv_file_path)
        combined_df = merge_with_tsv(combined_df, tsv_df)
    except Exception as e:
        print(f'Warning: Could not load or merge TSV file: {e}')
        print('Proceeding without TSV data')

    # Define column order (core fields first, then additional fields)
    core_columns = ['source_file', 'collection',
                    'yaml_entry_name', 'adapter_name', 'datafile', 'files_filesets_key', 'reference_filepath', 'notes', 'nested_context']
    other_fields = ['source', 'file_set_id', 'lab', 'label', 'biological_process', 'method', 'files_filesets_method', 'type', 'simple_sample_summaries', 'samples',
                    'source_annotation', 'molecular_function', 'version', 'threshold', 'relationship']

    # Reorder columns - only include columns that exist in the DataFrame
    column_order = [col for col in core_columns +
                    other_fields if col in combined_df.columns]
    combined_df = combined_df[column_order]

    # Create single Excel file with multiple sheets
    with pd.ExcelWriter(single_excel_file, engine='openpyxl') as writer:
        # Create master sheet with all data
        try:
            combined_df.to_excel(
                writer, sheet_name='ALL_COLLECTIONS', index=False)
            print(
                f'Created master sheet with {len(combined_df)} rows and {len(combined_df.columns)} columns')
        except Exception as e:
            print(f'Warning: Could not create master sheet: {e}')

        # Create sheets split by source values if source column exists
        if 'source' in combined_df.columns:
            # Create sheet for ENCODE
            encode_df = combined_df[combined_df['source'] == 'ENCODE']
            encode_df = drop_empty_columns(encode_df)
            if not encode_df.empty:
                encode_df.to_excel(writer, sheet_name='ENCODE', index=False)
                print(f'Created ENCODE sheet with {len(encode_df)} rows')
            else:
                print('No ENCODE data found')

            # Create sheet for IGVF
            igvf_df = combined_df[combined_df['source'] == 'IGVF']
            igvf_df = drop_empty_columns(igvf_df)
            if not igvf_df.empty:
                igvf_df.to_excel(writer, sheet_name='IGVF', index=False)
                print(f'Created IGVF sheet with {len(igvf_df)} rows')
            else:
                print('No IGVF data found')

            # Create sheet for External sources (everything not ENCODE or IGVF)
            other_sources_df = combined_df[~combined_df['source'].isin(
                ['ENCODE', 'IGVF'])]
            other_sources_df = drop_empty_columns(other_sources_df)
            if not other_sources_df.empty:
                other_sources_df.to_excel(
                    writer, sheet_name='External_sources', index=False)
                print(
                    f'Created External_sources sheet with {len(other_sources_df)} rows')
            else:
                print('No External sources data found')

    print(
        f'Created single Excel file with multiple sheets: {single_excel_file}')
    return combined_df


def main():
    yaml_files = ['data_sources.yaml', 'data_sources_SEMpl.yaml',
                  'data_sources_e2g_dnaseonly.yaml']
    tsv_file_path = 'files_filesets_0827.tsv'
    try:
        # Parse and create both single and individual Excel files
        result_df = parse_multiple_yaml_files(
            yaml_files,
            tsv_file_path,
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
                f"Entries with files_filesets_key: {result_df['files_filesets_key'].notna().sum()}")
            print(
                f"Entries with reference_filepath: {result_df['reference_filepath'].notna().sum()}")
            print(
                f"Entries with nested context: {result_df['nested_context'].notna().sum()}")
            print(
                f"Source files: {', '.join(result_df['source_file'].unique())}")
            print(
                f"Collections found: {', '.join(result_df['collection'].unique())}")
            print(f'Columns in final output: {list(result_df.columns)}')
            print(f'\nFiles created:')
            print(f'- Single Excel with all sheets: collections_summary.xlsx')
        else:
            print('No data was processed from any YAML files.')

    except Exception as e:
        print(f'Unexpected error: {e}')
        print('Please check your YAML file structures and ensure all required packages are installed.')


if __name__ == '__main__':
    main()
