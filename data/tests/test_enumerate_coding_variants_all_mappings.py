from data_loading_support_files.enumerate_coding_variants_all_mappings import enumerate_coding_variant

CHROM = 'chr1'
CHROM_REFSEQ = 'NC_000001.11'


class FakeSeqReader:
    '''py2bit-like reader over a few genome positions (0-based), N elsewhere'''

    def __init__(self, bases):
        self.bases = bases

    def sequence(self, chrom, start, end):
        return ''.join(self.bases.get(i, 'N') for i in range(start, end))


# + strand transcript: c.1-5 on genome 100-104, c.6- on genome 200-208,
# so codon 2 (c.4-6, GGC) spans the junction like ENSP00000263080 p.Gly79Val (GG|intron|C)
PLUS_EXONS = list(range(100, 105)) + list(range(200, 209))
PLUS_SEQ = FakeSeqReader(
    {100: 'A', 101: 'T', 102: 'G', 103: 'G', 104: 'G', 200: 'C', 201: 'G', 202: 'G', 203: 'C'})

# - strand transcript: c.1-5 on genome 304-300, c.6- on genome 199-191, codon 2 (c.4-6) on genome 301, 300, 199
MINUS_EXONS = list(reversed(range(300, 305))) + \
    list(reversed(range(191, 200)))
MINUS_SEQ = FakeSeqReader({301: 'C', 300: 'C', 199: 'G'})


def test_enumerate_coding_variant_skips_delins_spanning_junction():
    coding_variants = enumerate_coding_variant(
        'p.Gly2Val', 'GENE', 'ENST00000000001', '+', CHROM, CHROM_REFSEQ, PLUS_EXONS, PLUS_SEQ)

    # GTA, GTG, GTT need c.5_6delins across the junction, only the SNV c.5G>T is kept
    assert coding_variants['codon_ref'] == 'GGC'
    assert coding_variants['alt_codons'] == ['GTC']
    assert coding_variants['codon_positions'] == [2]
    assert coding_variants['hgvsc_ids'] == ['c.5G-T']
    assert coding_variants['mutation_ids'] == [
        'GENE_ENST00000000001_p.Gly2Val_c.5G-T']
    assert coding_variants['spdi_ids'] == ['NC_000001.11:104:G:T']
    assert coding_variants['hgvsg_ids'] == ['NC_000001.11:g.105G>T']


def test_enumerate_coding_variant_skips_delins_spanning_junction_minus_strand():
    coding_variants = enumerate_coding_variant(
        'p.Gly2Val', 'GENE', 'ENST00000000001', '-', CHROM, CHROM_REFSEQ, MINUS_EXONS, MINUS_SEQ)

    assert coding_variants['codon_ref'] == 'GGC'
    assert coding_variants['alt_codons'] == ['GTC']
    assert coding_variants['hgvsc_ids'] == ['c.5G-T']
    assert coding_variants['spdi_ids'] == ['NC_000001.11:300:C:A']


def test_enumerate_coding_variant_returns_none_when_all_alt_codons_span_junction():
    # GGC -> AAA, AAG: both need c.4_6delins across the junction
    assert enumerate_coding_variant(
        'p.Gly2Lys', 'GENE', 'ENST00000000001', '+', CHROM, CHROM_REFSEQ, PLUS_EXONS, PLUS_SEQ) is None


def test_enumerate_coding_variant_keeps_delins_within_exon():
    # codon 3 (c.7-9, GGC) is on genome 201-203, no junction
    coding_variants = enumerate_coding_variant(
        'p.Gly3Val', 'GENE', 'ENST00000000001', '+', CHROM, CHROM_REFSEQ, PLUS_EXONS, PLUS_SEQ)

    assert coding_variants['alt_codons'] == ['GTA', 'GTC', 'GTG', 'GTT']
    assert coding_variants['hgvsc_ids'] == [
        'c.8_9delinsTA', 'c.8G-T', 'c.8_9delinsTG', 'c.8_9delinsTT']
    assert coding_variants['spdi_ids'] == [
        'NC_000001.11:202:GC:TA', 'NC_000001.11:202:G:T', 'NC_000001.11:202:GC:TG', 'NC_000001.11:202:GC:TT']
