from biocommons.seqrepo import SeqRepo

seq_repo_human = None
seq_repo_mouse = None


def get_seqrepo(species='human'):
    global seq_repo_human, seq_repo_mouse
    if species == 'human':
        if seq_repo_human is None:
            seq_repo_human = SeqRepo('/usr/local/share/seqrepo/2018-11-26')
        return seq_repo_human
    else:
        if seq_repo_mouse is None:
            seq_repo_mouse = SeqRepo('/usr/local/share/seqrepo/mouse')
        return seq_repo_mouse


def is_variant_snv(spdi):
    spdi_list = spdi.split(':')
    if len(spdi_list) == 4 and len(spdi_list[2]) == 1 and len(spdi_list[3]) == 1:
        return True
    return False


def validate_snv_ref_seq_by_spdi(spdi, species='human'):
    seq_repo = get_seqrepo(species)
    spdi_list = spdi.split(':')
    chr_ref = spdi_list[0]
    start = int(spdi_list[1])
    end = start + 1
    ref = spdi_list[2]
    return ref == seq_repo[chr_ref][start:end]
