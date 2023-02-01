import yaml

from adapters import Adapter

# Example gnomad vcf input file:
##fileformat=VCFv4.2
##hailversion=0.2.77-684f32d73643
##FILTER=<ID=AC0,Description="Allele count is zero after filtering out low-confidence genotypes (GQ < 20; DP < 10; and AB < 0.2 for het calls)">
##FILTER=<ID=AS_VQSR,Description="Failed VQSR filtering thresholds of -2.7739 for SNPs and -1.0606 for indels">
##FILTER=<ID=InbreedingCoeff,Description="InbreedingCoeff < -0.3">
##FILTER=<ID=PASS,Description="Passed all variant filters">
##INFO=<ID=AC,Number=A,Type=Integer,Description="Alternate allele count">
##INFO=<ID=AN,Number=1,Type=Integer,Description="Total number of alleles">
##INFO=<ID=AF,Number=A,Type=Float,Description="Alternate allele frequency">
##INFO=<ID=popmax,Number=A,Type=String,Description="Population with maximum allele frequency">
# ...
# ##vep_version=v101
##dbsnp_version=b154
##age_distributions=bin_edges=[30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0], bin_freq=[1428, 1606, 1905, 3228, 4577, 3924, 3656, 3194, 2153, 1283], n_smaller=3760, n_larger=454
##contig=<ID=chr1,length=248956422,assembly=gnomAD_GRCh38>
##contig=<ID=chr2,length=242193529,assembly=gnomAD_GRCh38>
##contig=<ID=chr3,length=198295559,assembly=gnomAD_GRCh38>
# ...
# #CHROM  POS     ID      REF     ALT     QUAL    FILTER  INFO
# chrY    2781489 .       C       T       .       AC0     AC=0;AN=2716;AF=0.00000;AC_non_neuro_nfe=0;AN_non_neuro_nfe=1422;AF_non_neuro_nfe=0.00000;nhomalt_non_neuro_nfe=0;AC_non_neuro_afr_XY=0;AN_non_neuro_afr_XY=471;AF_non_neuro_afr_XY=0.00000;nhomalt_non_neuro_afr_XY=0;AC_non_neuro_nfe_XY=0;AN_non_neuro_nfe_XY=1422;AF_non_neuro_nfe_XY=0.0000 ...


class Gnomad(Adapter):
  DATASET = 'gnomad'
  ALLOWED_INFO_KEYS = set(['AC', 'AN', 'AF'])


  def __init__(self, chr='all', filepath=None, dry_run=True):
    self.filepath = filepath
    self.chr = chr
    self.dry_run = dry_run
    self.dataset = Gnomad.DATASET

    super(Gnomad, self).__init__()


  def parse_info_metadata(self, info):
    data = {}
    for pair in info.strip().split(';'):
      try:
        key, value = pair.split('=')
      except:
        if len(pair.split('=')) == 1:
          key = pair.split('=')[0]
          value = None

      if key in Gnomad.ALLOWED_INFO_KEYS:
        data[key] = value
    return data


  def process_file(self):
    headers = []
    reading_data = False
    
    for line in open(self.filepath, 'r'):

      if line.startswith('#CHROM'):
        headers = line.strip().split()
        reading_data = True
        continue

      if reading_data:
        data_line = line.strip().split()
        info = self.parse_info_metadata(data_line[headers.index('INFO')])

        _id = data_line[headers.index('#CHROM')] + data_line[headers.index('POS')]
        label = 'gnomad'
        _props = {
          'chr': data_line[headers.index('#CHROM')],
          'pos': data_line[headers.index('POS')],
          'id': data_line[headers.index('ID')],
          'ref': data_line[headers.index('REF')],
          'alt': data_line[headers.index('ALT')],
          'qual': data_line[headers.index('QUAL')],
          'filter': data_line[headers.index('FILTER')],
          'info': info
        }

        yield(_id, label, _props)

if __name__ == "__main__":
  adapter = Gnomad(filepath='./samples/gnomad_sample.vcf', chr='Y')
  adapter.print_ontology()
  adapter.write_file()
  print(adapter.arangodb())
