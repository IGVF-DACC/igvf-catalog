import pytest
from adapters.helpers import build_variant_id

def test_build_variant_id_fails_for_unsupported_assembly():
  with pytest.raises(ValueError, match='Assembly not supported'):
    build_variant_id(None, None, None, None, 'hg19')

  try:
    build_variant_id(None, None, None, None, 'GRCh38')
  except:
    assert False, 'build_variant_id raised exception for GRCh38'


def test_build_variant_id_creates_id_string():
  chr = 'chr'
  pos = 'pos'
  ref_seq = 'ref_seq'
  alt_seq = 'alt_seq'
  assembly = 'GRCh38'

  variant_id = build_variant_id(chr, pos, ref_seq, alt_seq, assembly)

  assert variant_id == '{}_{}_{}_{}_{}'.format(chr, pos, ref_seq, alt_seq, 'GRCh38')
