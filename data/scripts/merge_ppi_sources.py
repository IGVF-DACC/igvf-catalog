#!/usr/bin/env python3
"""Merge BioGRID + IntAct protein-protein-interaction sources into the
merged_PPI.UniProt.csv / merged_PPI_mouse.UniProt.csv format consumed by
data/adapters/proteins_interaction_adapter.py and
data/adapters/biogrid_gene_gene_adapter.py.

Usage:
    python3 data/scripts/merge_ppi_sources.py \
        --biogrid data/dataset/ppis/BIOGRID-ALL-5.0.263.tab3.txt \
        --intact-human data/dataset/ppis/human.txt \
        --intact-mouse data/dataset/ppis/mouse.txt \
        --out-human merged_PPI.UniProt.csv \
        --out-mouse merged_PPI_mouse.UniProt.csv \
        [--limit N]
"""
import argparse
import csv
import logging
import re
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger('merge_ppi_sources')

HEADER = [
    'Protein ID 1', 'Protein ID 2', 'PMID', 'Detection Method', 'Detection Method (PSI-MI)',
    'Interaction Type', 'Interaction Type (PSI-MI)', 'Confidence Value (biogrid)',
    'Confidence Value (intact)', 'Source'
]

# (detection_name, detection_code, interaction_name, interaction_code).
# Entries NOT in UNCONFIRMED_SYSTEMS were reverse-engineered directly from
# the real IGVFFI4317VDGK/IGVFFI1165YVBA example fixtures (cross-referencing
# exact pmid+pair matches against the raw BioGRID file) and are known-correct.
# Entries in UNCONFIRMED_SYSTEMS have no example in either fixture; they're a
# best-effort PSI-MI mapping and every row using one is logged for audit.
BIOGRID_PHYSICAL_MAP = {
    'Affinity Capture-Luminescence': ('affinity chromatography technology', 'MI:0004', 'physical association', 'MI:0915'),
    'Affinity Capture-MS': ('affinity chromatography technology', 'MI:0004', 'physical association', 'MI:0915'),
    'Affinity Capture-RNA': ('affinity chromatography technology', 'MI:0004', 'physical association', 'MI:0915'),
    'Affinity Capture-Western': ('affinity chromatography technology', 'MI:0004', 'physical association', 'MI:0915'),
    'Biochemical Activity': ('enzymatic study', 'MI:0415', 'direct interaction', 'MI:0407'),
    'Co-crystal Structure': ('x-ray crystallography', 'MI:0114', 'direct interaction', 'MI:0407'),
    'Co-fractionation': ('biochemical', 'MI:0401', 'colocalization', 'MI:0403'),
    'Co-localization': ('imaging technique', 'MI:0428', 'colocalization', 'MI:0403'),
    'Co-purification': ('biochemical', 'MI:0401', 'association', 'MI:0914'),
    'Cross-Linking-MS (XL-MS)': ('cross-linking study', 'MI:0030', 'direct interaction', 'MI:0407'),
    'Far Western': ('far western blotting', 'MI:0047', 'direct interaction', 'MI:0407'),
    'FRET': ('fluorescent resonance energy transfer', 'MI:0055', 'direct interaction', 'MI:0407'),
    'PCA': ('protein complementation assay', 'MI:0090', 'direct interaction', 'MI:0407'),
    'Protein-peptide': ('unspecified method', 'MI:0686', 'direct interaction', 'MI:0407'),
    'Protein-RNA': ('unspecified method', 'MI:0686', 'direct interaction', 'MI:0407'),
    'Proximity Label-MS': ('bioid', 'MI:1313', 'physical association', 'MI:0915'),
    'Reconstituted Complex': ('pull down', 'MI:0096', 'direct interaction', 'MI:0407'),
    'Surface Display': ('display technology', 'MI:0034', 'physical association', 'MI:0915'),
    'Thermal Shift Assay': ('thermal shift binding', 'MI:1235', 'direct interaction', 'MI:0407'),
    'Two-hybrid': ('two hybrid', 'MI:0018', 'direct interaction', 'MI:0407'),
}

UNCONFIRMED_SYSTEMS = {
    'Affinity Capture-Luminescence', 'Co-crystal Structure', 'PCA', 'Protein-RNA',
    'Surface Display', 'Thermal Shift Assay', 'Cross-Linking-MS (XL-MS)',
}

ORGANISM_TAXIDS = {'human': '9606', 'mouse': '10090'}

MI_TERM_RE = re.compile(r'psi-mi:"?(MI:\d+)"?\(([^)]*)\)')


def parse_mi_terms(field):
    return MI_TERM_RE.findall(field)


def biogrid_records(path, taxid, limit=None):
    """Yield (pair, detection_code, detection_name, interaction_code, interaction_name, [pmid], confidence)."""
    counts = defaultdict(int)
    with open(path, encoding='utf-8', errors='replace') as fh:
        fh.readline()
        for i, line in enumerate(fh):
            if limit is not None and i >= limit:
                break
            counts['read'] += 1
            row = line.rstrip('\n').split('\t')
            if len(row) < 29:
                counts['dropped_malformed'] += 1
                continue

            if row[15] != taxid or row[16] != taxid:
                counts['dropped_organism'] += 1
                continue

            swiss_a, swiss_b = row[23], row[26]
            if swiss_a == '-' or swiss_b == '-':
                counts['dropped_no_uniprot'] += 1
                continue
            if '|' in swiss_a or '|' in swiss_b:
                counts['multi_uniprot_took_first'] += 1
            protein_a = swiss_a.split('|')[0]
            protein_b = swiss_b.split('|')[0]
            if protein_a == protein_b:
                counts['dropped_self_interaction'] += 1
                continue

            exp_system, exp_type = row[11], row[12]
            if exp_type == 'genetic':
                # Genetic (detection method = 'genetic interference') rows are handled
                # by a separate gene-gene pipeline downstream, not this PPI merge.
                counts['dropped_genetic_interference'] += 1
                continue
            elif exp_type == 'physical':
                mapping = BIOGRID_PHYSICAL_MAP.get(exp_system)
                if mapping is None:
                    counts[f'unknown_physical_system:{exp_system}'] += 1
                    continue
                detection_name, detection_code, interaction_name, interaction_code = mapping
                if exp_system in UNCONFIRMED_SYSTEMS:
                    counts[f'unconfirmed_mapping:{exp_system}'] += 1
            else:
                counts[f'unknown_experimental_system_type:{exp_type}'] += 1
                continue

            pub = row[14]
            pmid = pub.split(':', 1)[1] if pub.startswith('PUBMED:') else pub
            score = row[18]
            confidence = score if score not in ('', '-') else ''

            pair = tuple(sorted((protein_a, protein_b)))
            counts['kept'] += 1
            yield pair, detection_code, detection_name, interaction_code, interaction_name, [pmid], confidence
    for key in sorted(counts):
        logger.info('biogrid[%s] %s: %d', taxid, key, counts[key])


def intact_records(path, taxid, limit=None):
    """Yield (pair, detection_code, detection_name, interaction_code, interaction_name, pmids, confidence)."""
    counts = defaultdict(int)
    taxid_marker = f'taxid:{taxid}('
    with open(path, encoding='utf-8', errors='replace') as fh:
        fh.readline()
        for i, line in enumerate(fh):
            if limit is not None and i >= limit:
                break
            counts['read'] += 1
            row = line.rstrip('\n').split('\t')
            if len(row) < 15:
                counts['dropped_malformed'] += 1
                continue

            id_a, id_b = row[0], row[1]
            if not id_a.startswith('uniprotkb:') or not id_b.startswith('uniprotkb:'):
                counts['dropped_no_uniprot'] += 1
                continue

            if taxid_marker not in row[9] or taxid_marker not in row[10]:
                counts['dropped_organism'] += 1
                continue

            if len(row) > 35 and row[35] == 'true':
                counts['dropped_negative'] += 1
                continue

            # Keep isoform suffixes (e.g. "Q9Y2R2-1") as-is rather than collapsing to the
            # canonical accession - IntAct's isoform-specific interactions are real, distinct
            # evidence and shouldn't be silently merged into their canonical protein's bucket.
            # BioGRID's SWISS-PROT accession columns never carry an isoform suffix, so this
            # only affects IntAct-sourced rows/buckets.
            protein_a = id_a.split(':', 1)[1]
            protein_b = id_b.split(':', 1)[1]
            if protein_a == protein_b:
                counts['dropped_self_interaction'] += 1
                continue

            detection_terms = parse_mi_terms(row[6])
            if not detection_terms:
                counts['dropped_no_detection_method'] += 1
                continue
            detection_code, detection_name = detection_terms[0]

            interaction_terms = parse_mi_terms(row[11])
            if not interaction_terms:
                counts['dropped_no_interaction_type'] += 1
                continue
            interaction_code, interaction_name = interaction_terms[0]

            pmids = [token.split(':', 1)[1] for token in row[8].split(
                '|') if token.startswith('pubmed:')]
            if not pmids:
                counts['dropped_no_pmid'] += 1
                continue

            confidence = ''
            for token in row[14].split('|'):
                if token.startswith('intact-miscore:'):
                    confidence = token.split(':', 1)[1]
                    break

            pair = tuple(sorted((protein_a, protein_b)))
            counts['kept'] += 1
            yield pair, detection_code, detection_name, interaction_code, interaction_name, pmids, confidence
    for key in sorted(counts):
        logger.info('intact[%s] %s: %d', taxid, key, counts[key])


def build_buckets(records):
    """Group records by (pair, detection_code); fold in every raw row sharing that key."""
    buckets = {}
    for pair, det_code, det_name, int_code, int_name, pmids, confidence in records:
        key = (pair, det_code)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {'detection_name': det_name,
                      'interaction_types': [], 'pmids': [], 'confidence': ''}
            buckets[key] = bucket
        if (int_code, int_name) not in bucket['interaction_types']:
            bucket['interaction_types'].append((int_code, int_name))
        bucket['pmids'].extend(pmids)
        if not bucket['confidence'] and confidence:
            bucket['confidence'] = confidence
    return buckets


def merge_buckets(biogrid_buckets, intact_buckets):
    rows = []
    merged_count = 0
    biogrid_only_count = 0
    intact_only_count = 0
    for key in set(biogrid_buckets) | set(intact_buckets):
        pair, det_code = key
        bg = biogrid_buckets.get(key)
        ia = intact_buckets.get(key)

        if bg and ia:
            det_name = bg['detection_name']
            pmids = bg['pmids'] + ia['pmids']
            interaction_types = list(ia['interaction_types'])
            for t in bg['interaction_types']:
                if t not in interaction_types:
                    interaction_types.append(t)
            conf_bg, conf_ia = bg['confidence'], ia['confidence']
            source = 'IntAct; BioGRID'
            merged_count += 1
        elif bg:
            det_name = bg['detection_name']
            pmids = bg['pmids']
            interaction_types = bg['interaction_types']
            conf_bg, conf_ia = bg['confidence'], ''
            source = 'BioGRID'
            biogrid_only_count += 1
        else:
            det_name = ia['detection_name']
            pmids = ia['pmids']
            interaction_types = ia['interaction_types']
            conf_bg, conf_ia = '', ia['confidence']
            source = 'IntAct'
            intact_only_count += 1

        interaction_name = '; '.join(name for _, name in interaction_types)
        interaction_code = '; '.join(code for code, _ in interaction_types)
        rows.append([
            pair[0], pair[1], '[' + ', '.join(pmids) + ']', det_name, det_code,
            interaction_name, interaction_code, conf_bg, conf_ia, source
        ])

    logger.info('merged: %d, biogrid-only: %d, intact-only: %d, total rows: %d',
                merged_count, biogrid_only_count, intact_only_count, len(rows))
    return rows


def write_csv(path, rows):
    with open(path, 'w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        writer.writerows(rows)
    logger.info('wrote %d rows to %s', len(rows), path)


def run_organism(organism, biogrid_path, intact_path, out_path, limit=None):
    taxid = ORGANISM_TAXIDS[organism]
    logger.info('=== %s (taxid %s) ===', organism, taxid)
    biogrid_buckets = build_buckets(
        biogrid_records(biogrid_path, taxid, limit=limit))
    intact_buckets = build_buckets(
        intact_records(intact_path, taxid, limit=limit))
    rows = merge_buckets(biogrid_buckets, intact_buckets)
    write_csv(out_path, rows)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--biogrid', required=True,
                        help='Path to BIOGRID-ALL-*.tab3.txt')
    parser.add_argument('--intact-human', required=True,
                        help='Path to IntAct human.txt')
    parser.add_argument('--intact-mouse', required=True,
                        help='Path to IntAct mouse.txt')
    parser.add_argument('--out-human', required=True,
                        help='Output path for merged_PPI.UniProt.csv')
    parser.add_argument('--out-mouse', required=True,
                        help='Output path for merged_PPI_mouse.UniProt.csv')
    parser.add_argument('--limit', type=int, default=None,
                        help='Only read the first N lines of each input file (dry-run)')
    args = parser.parse_args()

    run_organism('human', args.biogrid, args.intact_human,
                 args.out_human, limit=args.limit)
    run_organism('mouse', args.biogrid, args.intact_mouse,
                 args.out_mouse, limit=args.limit)


if __name__ == '__main__':
    main()
