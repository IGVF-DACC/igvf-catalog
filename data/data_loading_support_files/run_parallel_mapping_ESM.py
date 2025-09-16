import gzip
import csv
import py2bit
import sys
import time
import traceback
from multiprocessing import Pool
from functools import partial
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import argparse
import resource
import signal
import enumerate_coding_variants_all_mappings
import os
import gc

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
API_TIMEOUT = 60  # seconds
CHUNK_SIZE = 10

# Configure logging


def setup_logging():
    import logging
    from logging.handlers import RotatingFileHandler

    # Create a logger
    logger = logging.getLogger()
    # Set to lowest level to handle all messages
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # INFO handler - writes to info.log
    info_handler = RotatingFileHandler(
        'info.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(lambda record: record.levelno == logging.INFO)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

    # WARNING handler - writes to warning.log
    warning_handler = RotatingFileHandler(
        'warning.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(lambda record: record.levelno == logging.WARNING)
    warning_handler.setFormatter(formatter)
    logger.addHandler(warning_handler)

    # ERROR handler - writes to error.log
    error_handler = RotatingFileHandler(
        'error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Also add a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()

# Configure requests session with retries


def create_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Global session object
api_session = create_session()

# Signal handler for graceful termination


def setup_signal_handlers():
    def handle_signal(signum, frame):
        logger.critical(f'Received termination signal {signum}')
        logger.info('Attempting graceful shutdown...')
        sys.exit(1)

    signals = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]
    for sig in signals:
        signal.signal(sig, handle_signal)

# Resource monitoring


def log_resource_usage():
    mem = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)  # in MB
    logger.info(f'Memory usage: {mem:.2f} MB')
    logger.info(
        f'CPU time: {resource.getrusage(resource.RUSAGE_SELF).ru_utime:.2f}s')


# Chromosome mapping
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


def init_worker(two_bit_path):
    """Initialize worker with a 2bit reader instance."""
    global worker_seq_reader
    try:
        worker_seq_reader = py2bit.open(two_bit_path)
        logger.info(f'Worker initialized with 2bit file at {two_bit_path}')
    except Exception as e:
        logger.error(f'Failed to initialize worker: {str(e)}')
        raise


def get_protein_id_name(transcript_id):
    transcript_id = transcript_id.split('.')[0]
    query_url = f'https://api-dev.catalog.igvf.org/api/transcripts/proteins?transcript_id={transcript_id}&organism=Homo%20sapiens&verbose=true'
    protein_id = ''
    protein_name = ''
    try:
        response = api_session.get(query_url, timeout=API_TIMEOUT)
        response.raise_for_status()
        responses = response.json()

        if not responses:
            logger.warning(f'No protein mapping to {transcript_id}')
            return None, None
        else:
            if len(responses[0]['protein']) > 1:
                logger.warning(
                    f'Multiple protein ids mapping to {transcript_id}')
            if len(responses[0]['protein'][0]['names']) > 1:
                logger.warning(
                    f'Multiple protein names mapping to {transcript_id}')

            protein_id = responses[0]['protein'][0]['_id']
            protein_name = responses[0]['protein'][0]['names'][0]
    except Exception as e:
        logger.error(
            f'Failed to get protein mapping for {transcript_id}: {str(e)}')
        logger.debug(traceback.format_exc())
    return protein_id, protein_name


def get_exon_coordinates(transcript_id):
    """Fetch exon coordinates with retries and error handling."""
    transcript_id = transcript_id.split('.')[0]
    query_url = f'https://api-dev.catalog.igvf.org/api/genes-structure?transcript_id={transcript_id}&organism=Homo%20sapiens&limit=1000'

    exons_coordinates = []
    chrom = None
    chrom_refseq = None
    strand = None
    CDS = {}

    try:
        start_time = time.time()
        response = api_session.get(query_url, timeout=API_TIMEOUT)
        response.raise_for_status()
        responses = response.json()

        # Process response
        for structure in responses:
            if structure['type'] == 'CDS':
                CDS[int(structure['exon_number'])] = structure

        # Validate we got CDS data
        if not CDS:
            logger.warning(f'No CDS data found for {transcript_id}')
            return None, None, None, None

        # Sort and process exons
        for i in range(min(CDS.keys()), max(CDS.keys())+1):
            if i not in CDS:
                logger.warning(f'Missing exon {i} in {transcript_id}')
                continue

            if CDS[i]['strand'] == '+':
                exons_coordinates.extend(range(CDS[i]['start'], CDS[i]['end']))
            else:
                exons_coordinates.extend(
                    reversed(range(CDS[i]['start'], CDS[i]['end'])))

        # Validate CDS length
        if len(exons_coordinates) % 3 != 0:
            logger.warning(
                f'CDS length not divisible by 3 for {transcript_id}: {len(exons_coordinates)}')

        chrom = responses[0]['chr']
        chrom_refseq = CHR_MAP.get(chrom)
        strand = responses[0]['strand']
        gene_symbol = responses[0]['gene_name']

        logger.debug(
            f'Processed {transcript_id} in {time.time()-start_time:.2f}s')
        return exons_coordinates, chrom, chrom_refseq, strand, gene_symbol

    except Exception as e:
        logger.error(
            f'Failed to get coordinates for {transcript_id}: {str(e)}')
        logger.debug(traceback.format_exc())
        return None, None, None, None, None
    finally:

        gc.collect()


def process_transcript_batch(args):
    """Process a batch of rows for a single transcript with comprehensive error handling."""
    transcript_id, rows = args
    batch_results = []

    try:
        start_time = time.time()
        logger.info(f'Processing {transcript_id} with {len(rows)} variants')
        # Get protein id and protein name
        protein_id, protein_name = get_protein_id_name(transcript_id)

        # Get coordinates
        exons_coordinates, chrom, chrom_refseq, strand, gene_symbol = get_exon_coordinates(
            transcript_id)
        if chrom is None or '_' in chrom:
            logger.warning(f'Skipping {transcript_id} - invalid coordinates')
            return []

        # Process each variant
        for row_idx, row in enumerate(rows):
            try:
                gene_id, _, protein_id, hgvsp = row[:4]
                scores = row[4:]
                hgvsp = hgvsp.split(':')[1]
                coding_variants = enumerate_coding_variants_all_mappings.enumerate_coding_variant(
                    hgvsp, gene_symbol, transcript_id, strand, chrom, chrom_refseq,
                    exons_coordinates, worker_seq_reader)

                if coding_variants:
                    batch_results.append((
                        transcript_id, hgvsp,
                        ','.join(coding_variants['mutation_ids']),
                        ','.join(coding_variants['hgvsc_ids']),
                        ','.join(coding_variants['spdi_ids']),
                        ','.join(coding_variants['hgvsg_ids']),
                        ','.join(coding_variants['alt_codons']),
                        ','.join(str(p)
                                 for p in coding_variants['codon_positions']),
                        coding_variants['codon_ref'],
                        protein_id,
                        protein_name,
                        *scores
                    ))

            except ValueError as ve:
                logger.error(
                    f'Error processing variant {row_idx} in {transcript_id}: {str(ve)}')
            except Exception as var_err:
                logger.error(
                    f'Error processing variant {row_idx} in {transcript_id}: {str(var_err)}')
                logger.debug(traceback.format_exc())
                continue

        logger.info(
            f'Completed {transcript_id} in {time.time()-start_time:.2f}s')
        return batch_results

    except Exception as batch_err:
        logger.error(
            f'Fatal error processing batch {transcript_id}: {str(batch_err)}')
        logger.debug(traceback.format_exc())
        return []
    finally:
        del batch_results
        gc.collect()


def stream_transcript_batches(input_file):
    """Generator that yields transcript batches with error handling."""
    try:
        with gzip.open(input_file, 'rt') as esm_file:
            esm_csv = csv.reader(esm_file, delimiter='\t')
            next(esm_csv)  # Skip header

            current_transcript = None
            current_batch = []

            for row_idx, row in enumerate(esm_csv):
                try:
                    transcript_id = row[1]

                    if transcript_id != current_transcript:
                        if current_batch:
                            yield (current_transcript, current_batch)
                            current_batch = []
                        current_transcript = transcript_id
                    current_batch.append(row)

                except Exception as row_err:
                    logger.error(
                        f'Error processing row {row_idx}: {str(row_err)}')
                    continue

            if current_batch:
                yield (current_transcript, current_batch)

    except Exception as file_err:
        logger.critical(f'Failed to read input file: {str(file_err)}')
        raise


def parallel_process_streaming(input_file, output_file, two_bit_path, num_processes=4):
    """Main parallel processing function with robust error handling."""
    setup_signal_handlers()
    logger.info(f'Starting parallel processing with {num_processes} workers')

    try:
        with Pool(
            processes=num_processes,
            initializer=init_worker,
            initargs=(two_bit_path,),
            maxtasksperchild=1  # Prevent memory leaks
        ) as pool, gzip.open(output_file, 'wt') as outfile:

            # Process transcripts in streaming batches
            results_gen = pool.imap_unordered(
                process_transcript_batch,
                stream_transcript_batches(input_file),
                chunksize=CHUNK_SIZE
            )

            # Write results with error handling
            processed = 0
            for result_batch in results_gen:
                try:
                    for line in result_batch:
                        outfile.write('\t'.join(line) + '\n')
                    processed += len(result_batch)
                    if processed % 1000 == 0:
                        logger.info(f'Processed {processed} variants')
                        log_resource_usage()
                except Exception as write_err:
                    logger.error(f'Failed to write results: {str(write_err)}')
                    continue

        logger.info(
            f'Processing complete. Total variants processed: {processed}')

    except Exception as main_err:
        logger.critical(f'Fatal error in parallel processing: {str(main_err)}')
        logger.critical(traceback.format_exc())
        sys.exit(1)
    finally:
        log_resource_usage()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='Input file path')
    parser.add_argument('--output', '-o', required=True,
                        help='Output file path')
    parser.add_argument('--two_bit', required=True, help='Path to 2bit file')
    parser.add_argument('--processes', '-p', type=int,
                        default=4, help='Number of parallel processes')
    args = parser.parse_args()

    try:
        logger.info(f'Starting processing at {datetime.now()}')
        parallel_process_streaming(
            args.input,
            args.output,
            args.two_bit,
            num_processes=args.processes
        )
        logger.info(f'Processing completed successfully at {datetime.now()}')
    except Exception as e:
        logger.critical(f'Script failed: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
