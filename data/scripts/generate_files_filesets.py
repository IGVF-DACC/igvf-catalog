"""
Generate files_filesets JSONL outputs using FileFileSet adapter.

Purpose:
  Reads file accessions from data/data_sources/data_sources_file_fileset.yaml and
  writes JSONL files for files_filesets, donors, and sample terms (IGVF + ENCODE).

Output:
  By default outputs to data/parsed_data with names like:
    igvf_files_filesets_YYYYMMDDTHHMMSSZ.jsonl
    encode_files_filesets_YYYYMMDDTHHMMSSZ.jsonl
    igvf_donors_YYYYMMDDTHHMMSSZ.jsonl
    encode_donors_YYYYMMDDTHHMMSSZ.jsonl
    igvf_sample_terms_YYYYMMDDTHHMMSSZ.jsonl
    encode_sample_terms_YYYYMMDDTHHMMSSZ.jsonl

Usage:
  python3 data/scripts/generate_files_filesets.py
  python3 data/scripts/generate_files_filesets.py --label igvf_file_fileset
  python3 data/scripts/generate_files_filesets.py --label encode_donor
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(REPO_ROOT / 'data'))

from adapters.file_fileset_adapter import FileFileSet  # noqa: E402
from adapters.writer import LocalWriter  # noqa: E402


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
    parser.add_argument(
        '--label',
        choices=list(FileFileSet.ALLOWED_LABELS),
        help='Run a single label. If omitted, runs all labels.'
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
        'encode_file_fileset': f'encode_files_filesets_{timestamp}.jsonl',
        'igvf_donor': f'igvf_donors_{timestamp}.jsonl',
        'encode_donor': f'encode_donors_{timestamp}.jsonl',
        'igvf_sample_term': f'igvf_sample_terms_{timestamp}.jsonl',
        'encode_sample_term': f'encode_sample_terms_{timestamp}.jsonl'
    }

    igvf_accessions = unique_preserve_order(
        collect_accessions(data_sources.get('igvf_file_accessions', {}))
    )
    encode_accessions = unique_preserve_order(
        collect_accessions(data_sources.get('encode_file_accessions', {}))
    )

    labels_to_run = (
        {args.label: labels[args.label]} if args.label else labels
    )

    for label, filename in labels_to_run.items():
        accessions = igvf_accessions if label.startswith(
            'igvf_') else encode_accessions
        output_path = str(output_dir / filename)
        destination = generate_files_filesets(accessions, label, output_path)
        print(f'Wrote {label} to {destination}')


if __name__ == '__main__':
    main()
