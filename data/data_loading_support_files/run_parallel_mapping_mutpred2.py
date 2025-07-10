import gzip
import csv
import py2bit
from multiprocessing import Pool

import enumerate_coding_variants_all_mappings
import requests
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', help='input file path')
parser.add_argument('--output', '-o', help='output file path')


def init_worker(two_bit_path):
    """Initialize worker with a 2bit reader instance."""
    global worker_seq_reader
    worker_seq_reader = py2bit.open(two_bit_path)


def process_transcript_batch(args):
    """Process a batch of rows for a single transcript."""
    transcript_id, rows = args
    try:
        exons_coordinates, chrom, chrom_refseq, strand = get_exon_coordinates(
            transcript_id)
        if chrom is None or '_' in chrom:
            print(
                f'Skipping {transcript_id} - no coordinates or invalid chrom')
            return []

        results = []
        for row in rows:
            protein_id, _, gene_id, gene_symbol, hgvsp, score, properties = row
            coding_variants = enumerate_coding_variants_all_mappings.enumerate_coding_variant(
                hgvsp, gene_symbol, transcript_id, strand, chrom, chrom_refseq,
                exons_coordinates, worker_seq_reader)

            if coding_variants:
                results.append((
                    transcript_id, hgvsp,
                    ','.join(coding_variants['mutation_ids']),
                    ','.join(coding_variants['hgvsc_ids']),
                    ','.join(coding_variants['spdi_ids'])
                ))
        return results
    except Exception as e:
        print(f'Error processing {transcript_id}: {str(e)}')
        return []


def stream_transcript_batches(input_file):
    """Generator that yields transcript batches one at a time."""
    with gzip.open(input_file, 'rt') as mutpred_file:
        mutpred_csv = csv.reader(mutpred_file, delimiter='\t')
        next(mutpred_csv)  # Skip header

        current_transcript = None
        current_batch = []

        for row in mutpred_csv:
            transcript_id = row[1]

            if transcript_id != current_transcript:
                if current_batch:
                    yield (current_transcript, current_batch)
                    current_batch = []
                current_transcript = transcript_id
            current_batch.append(row)

        if current_batch:
            yield (current_transcript, current_batch)


def parallel_process_streaming(input_file, output_file, two_bit_path, num_processes=4, batch_size=1000):
    """Process input file in parallel with minimal memory usage."""
    with Pool(
        processes=num_processes,
        initializer=init_worker,
        initargs=(two_bit_path,)
    ) as pool, gzip.open(output_file, 'wt') as outfile:

        # Process transcripts in streaming batches
        results_gen = pool.imap(
            process_transcript_batch,
            stream_transcript_batches(input_file),
            chunksize=batch_size
        )

        # Write results as they're generated
        for result_batch in results_gen:
            for line in result_batch:
                outfile.write('\t'.join(line) + '\n')


def get_exon_coordinates(transcript_id):
    transcript_id = transcript_id.split('.')[0]
    # double check limit
    query_url = f'https://api-dev.catalog.igvf.org/api/genes-structure?transcript_id={transcript_id}&organism=Homo%20sapiens&limit=1000'
    exons_coordinates = []
    chrom = None
    chrom_refseq = None
    strand = None
    CDS = {}
    try:
        responses = requests.get(query_url).json()
    # get gene structure from KG; the exon ranges are stored in bed format
        for structure in responses:
            if structure['type'] == 'CDS':
                CDS[int(structure['exon_number'])] = structure
        # sort by exon_number, not necessarily start from 1
        for i in range(min(CDS.keys()), max(CDS.keys())+1):
            if CDS[i]['strand'] == '+':
                exons_coordinates.extend(
                    list(range(CDS[i]['start'], CDS[i]['end'])))
            else:  # on reverse strand
                exons_coordinates.extend(
                    list(reversed(range(CDS[i]['start'], CDS[i]['end']))))
        # sanity check on exon CDS total length
        if len(exons_coordinates) % 3 != 0:
            print('Warning: ' + transcript_id +
                  ' CDS length is ' + str(len(exons_coordinates)))
        chrom = responses[0]['chr']
        chrom_refseq = CHR_MAP[chrom]
        strand = responses[0]['strand']
    except Exception as e:
        print(f'Error: {e}')

    return exons_coordinates, chrom, chrom_refseq, strand


CHR_MAP = {
    'chr1': 'NC_000001.11',
    '1': 'NC_000001.11',
    'chr2': 'NC_000002.12',
    '2': 'NC_000002.12',
    'chr3': 'NC_000003.12',
    '3': 'NC_000003.12',
    'chr4': 'NC_000004.12',
    '4': 'NC_000004.12',
    'chr5': 'NC_000005.10',
    '5': 'NC_000005.10',
    'chr6': 'NC_000006.12',
    '6': 'NC_000006.12',
    'chr7': 'NC_000007.14',
    '7': 'NC_000007.14',
    'chr8': 'NC_000008.11',
    '8': 'NC_000008.11',
    'chr9': 'NC_000009.12',
    '9': 'NC_000009.12',
    'chr10': 'NC_000010.11',
    '10': 'NC_000010.11',
    'chr11': 'NC_000011.10',
    '11': 'NC_000011.10',
    'chr12': 'NC_000012.12',
    '12': 'NC_000012.12',
    'chr13': 'NC_000013.11',
    '13': 'NC_000013.11',
    'chr14': 'NC_000014.9',
    '14': 'NC_000014.9',
    'chr15': 'NC_000015.10',
    '15': 'NC_000015.10',
    'chr16': 'NC_000016.10',
    '16': 'NC_000016.10',
    'chr17': 'NC_000017.11',
    '17': 'NC_000017.11',
    'chr18': 'NC_000018.10',
    '18': 'NC_000018.10',
    'chr19': 'NC_000019.10',
    '19': 'NC_000019.10',
    'chr20': 'NC_000020.11',
    '20': 'NC_000020.11',
    'chr21': 'NC_000021.9',
    '21': 'NC_000021.9',
    'chr22': 'NC_000022.11',
    '22': 'NC_000022.11',
    'chrX': 'NC_000023.11',
    'X': 'NC_000023.11',
    '23': 'NC_000023.11',
    'chrY': 'NC_000024.10',
    'Y': 'NC_000024.10',
    '24': 'NC_000024.10'
}


def main():

    parallel_process_streaming(
        'new_exclude_nonhuman/IGVFFI6893ZOAA.tsv.gz',
        'IGVFFI6893ZOAA_all_mappings_parallel.tsv.gz',
        'hg38.2bit',
        num_processes=8
    )


if __name__ == '__main__':
    main()
