import csv

from adapters import Adapter
from adapters.helpers import build_variant_id

# Example QTEx eQTL input file:
# variant_id      gene_id tss_distance    ma_samples      ma_count        maf     pval_nominal    slope   slope_se        pval_nominal_threshold  min_pval_nominal        pval_beta
# chr1_845402_A_G_b38     ENSG00000225972.1       216340  4       4       0.0155039       2.89394e-06     2.04385 0.413032        2.775e-05       2.89394e-06     0.00337661
# chr1_920569_G_A_b38     ENSG00000225972.1       291507  4       4       0.0155039       1.07258e-05     1.92269 0.415516        2.775e-05       2.89394e-06     0.00337661


class EQtl(Adapter):
  # 1-based coordinate system

  DATASET = 'qtl'

  def __init__(self, filepath, biological_context):
    self.filepath = filepath
    self.biological_context = biological_context
    self.dataset = EQtl.DATASET
    
    super(EQtl, self).__init__()


  def process_file(self):
    with open(self.filepath, 'r') as qtl:
      qtl_csv = csv.reader(qtl, delimiter = '\t')

      next(qtl_csv)

      for row in qtl_csv:
        chr, pos, ref_seq, alt_seq, assembly_code = row[0].split('_')

        if assembly_code != 'b38':
          print('Unsuported assembly: ' + assembly_code)
          continue
        
        variant_id = build_variant_id(
          chr, pos, ref_seq, alt_seq, 'GRCh38'
        )

        try:
          _id = row[2] + row[3]
          _source = 'variants/' + variant_id
          _target = 'genes/' + row[1]
          label = 'qtl'
          _props = {
            'biological_context': self.biological_context,
            'chr': chr,
            'p-value': row[6],
            'slope': row[7],
            'beta': row[-1]
          }

          yield(_id, _source, _target, label, _props)
        except:
          print(row)
          pass
