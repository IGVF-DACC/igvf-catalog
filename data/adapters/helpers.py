def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
  if assembly != 'GRCh38':
    raise ValueError("Assembly not supported")

  return '{}_{}_{}_{}_{}'.format(chr, pos_first_ref_base, ref_seq, alt_seq, assembly)
