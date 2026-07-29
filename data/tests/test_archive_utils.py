import gzip
import io
import tarfile
import zipfile

import pytest

from adapters.archive_utils import (
    get_file_accession,
    get_files_from_folder,
)


def test_double_gzipped_tar_extraction(tmp_path):
    # Mirrors the pharmGKB portal file, which is a gzip of (tar.gz).
    inner_tar_gz = tmp_path / 'inner.tar.gz'
    with tarfile.open(inner_tar_gz, 'w:gz') as archive:
        payload = b'anno\n'
        member = tarfile.TarInfo('pharmGKB/var_drug_ann.tsv')
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

    filepath = tmp_path / 'IGVFFI8835SMSP.tar.gz'
    with open(inner_tar_gz, 'rb') as source:
        filepath.write_bytes(gzip.compress(source.read()))

    extracted_files = {
        path.name: path.read_text()
        for path in get_files_from_folder(str(filepath))
    }
    assert extracted_files == {'var_drug_ann.tsv': 'anno\n'}


def test_nested_archive_extraction_and_accession(tmp_path):
    nested_zip = tmp_path / 'adastra.zip'
    with zipfile.ZipFile(nested_zip, 'w') as archive:
        archive.writestr('release/data/example.tsv', 'header\nvalue\n')

    filepath = tmp_path / 'IGVFFI0000TEST.tar.gz'
    with tarfile.open(filepath, 'w:gz') as archive:
        archive.add(nested_zip, arcname=nested_zip.name)

    assert get_file_accession(str(filepath)) == 'IGVFFI0000TEST'

    extracted_files = {
        path.name: path.read_text()
        for path in get_files_from_folder(str(filepath))
        if path.suffix == '.tsv'
    }
    assert extracted_files == {'example.tsv': 'header\nvalue\n'}


def test_archive_path_traversal_is_rejected(tmp_path):
    filepath = tmp_path / 'IGVFFI0000TEST.tar.gz'
    with tarfile.open(filepath, 'w:gz') as archive:
        member = tarfile.TarInfo('../outside.txt')
        contents = b'not safe'
        member.size = len(contents)
        archive.addfile(member, io.BytesIO(contents))

    with pytest.raises(ValueError, match='escapes the extraction directory'):
        list(get_files_from_folder(str(filepath)))


def test_missing_accession_in_filename(tmp_path):
    filepath = tmp_path / 'pwm.tar.gz'
    with tarfile.open(filepath, 'w:gz') as archive:
        archive.add(tmp_path, arcname='.')

    with pytest.raises(ValueError, match='Could not derive'):
        get_file_accession(str(filepath))
