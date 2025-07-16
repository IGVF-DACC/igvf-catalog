import gzip
import csv

from adapters.helpers import bulk_check_caid_in_arangodb


def process_variant_chunk(chunk):
    loaded_caids = bulk_check_caid_in_arangodb([row[3] for row in chunk])
    unloaded_caids = []

    for row in chunk:
        if row[3] not in loaded_caids:
            unloaded_caids.append(row[3])
            print(row[3])
    return unloaded_caids


with gzip.open('IGVFFI0407TIWL.tsv.gz', 'rt') as variant_file:
    reader = csv.reader(variant_file, delimiter='\t')
    next(reader)
    chunk_size = 6000

    chunk = []
    unloaded_caids_all = []
    caids_all = []
    for i, row in enumerate(reader, 1):
        chunk.append(row)
        if i % chunk_size == 0:
            unloaded_caids = process_variant_chunk(chunk)
            unloaded_caids_all.extend(unloaded_caids)
            chunk = []

    if chunk != []:
        unloaded_caids = process_variant_chunk(chunk)
        unloaded_caids_all.extend(unloaded_caids)

    print(f'{len(unloaded_caids)} variants not found with caid')
