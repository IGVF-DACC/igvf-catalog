"""
Generate files_filesets JSONL outputs using FileFileSet adapter.

Purpose:
  Reads file accessions from data/data_sources/data_sources_file_fileset.yaml and
  writes two JSONL files (IGVF + ENCODE) for the files_filesets collection.

Output:
  By default outputs to data/parsed_data with names like:
    igvf_files_filesets_YYYYMMDDTHHMMSSZ.jsonl
    encode_files_filesets_YYYYMMDDTHHMMSSZ.jsonl

Usage:
  python3 data/scripts/generate_files_filesets.py
"""

from adapters.writer import LocalWriter
from adapters.file_fileset_adapter import FileFileSet
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(REPO_ROOT / 'data'))


def collect_accessions(value):
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, dict):
        accessions = []
        for nested_value in value.values():
            accessions.extend(collect_accessions(nested_value))
        return accessions
    if isinstance(value, str):
        return [value]
    return []

# remove duplicates while preserving order, can be helpful if we want to perform git diff between two versions of the same file


def unique_preserve_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def generate_files_filesets(accessions, label, output_path):
    writer = LocalWriter(output_path)
    adapter = FileFileSet(
        accessions=accessions,
        label=label,
        writer=writer,
        replace=True,
        validate=True
    )
    adapter.process_file()
    return writer.destination


def main():
    parser = argparse.ArgumentParser(
        description='Generate files_filesets jsonl outputs.')
    parser.add_argument(
        '--data-sources-file',
        default='data/data_sources/data_sources_file_fileset.yaml',
        help='Path to data_sources_file_fileset.yaml'
    )
    parser.add_argument(
        '--output-dir',
        default='data/parsed_data',
        help='Directory to write generated jsonl files'
    )
    args = parser.parse_args()

    data_sources_path = Path(args.data_sources_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with data_sources_path.open('r') as handle:
        data_sources = yaml.safe_load(handle)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    labels = {
        'igvf_file_fileset': f'igvf_files_filesets_{timestamp}.jsonl',
        'encode_file_fileset': f'encode_files_filesets_{timestamp}.jsonl'
    }

    for label, filename in labels.items():
        accessions_key = f"{label.split('_')[0]}_file_accessions"
        accessions_data = data_sources.get(accessions_key, {})
        accessions = unique_preserve_order(collect_accessions(accessions_data))
        output_path = str(output_dir / filename)
        destination = generate_files_filesets(accessions, label, output_path)
        print(f'Wrote {label} to {destination}')


if __name__ == '__main__':
    main()
