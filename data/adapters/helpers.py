from inspect import getfullargspec

ALLOWED_ASSEMBLIES = ['GRCh38']

def assembly_check(id_builder):
  def wrapper(*args, **kwargs):
    argspec = getfullargspec(id_builder)

    if 'assembly' in argspec.args:
      assembly_index = argspec.args.index('assembly')
      if assembly_index >= len(args):
        pass
      elif args[assembly_index] not in ALLOWED_ASSEMBLIES:
        raise ValueError("Assembly not supported")
    return id_builder(*args, *kwargs)

  return wrapper

@assembly_check
def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
  # pos_first_ref_base: 1-based position
  return '{}_{}_{}_{}_{}'.format(chr, pos_first_ref_base, ref_seq, alt_seq, assembly)

@assembly_check
def build_open_chromatic_region_id(chr, pos_start, pos_end, assembly='GRCh38'):
  return '{}_{}_{}_{}'.format(chr, pos_start, pos_end, assembly)