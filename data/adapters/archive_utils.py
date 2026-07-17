import gzip
import os
import re
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Iterator


FILE_ACCESSION_PATTERN = re.compile(r'(?:IGVFFI|ENCFF)[A-Z0-9]+')


def get_file_accession(filepath: str) -> str:
    """Derive the file accession from the input archive filename."""
    match = FILE_ACCESSION_PATTERN.search(Path(filepath).name)
    if match:
        return match.group(0)

    raise ValueError(
        'Could not derive the file accession from filepath. Pass an archive '
        'whose filename contains an IGVFFI or ENCFF accession.'
    )


def _validated_destination(directory: Path, member_name: str) -> Path:
    destination = (directory / member_name).resolve()
    directory = directory.resolve()
    if os.path.commonpath((str(directory), str(destination))) != str(directory):
        raise ValueError(
            f'Archive member escapes the extraction directory: {member_name}'
        )
    return destination


def _is_gzip(filepath: Path) -> bool:
    try:
        with open(filepath, 'rb') as handle:
            return handle.read(2) == b'\x1f\x8b'
    except OSError:
        return False


def _is_archive(filepath: Path) -> bool:
    return (
        tarfile.is_tarfile(filepath)
        or zipfile.is_zipfile(filepath)
        or _is_gzip(filepath)
    )


def _extract_tar(filepath: Path, destination: Path) -> None:
    with tarfile.open(filepath) as archive:
        members = archive.getmembers()
        for member in members:
            _validated_destination(destination, member.name)
            if member.issym() or member.islnk() or member.isdev():
                raise ValueError(
                    f'Unsupported archive member type: {member.name}'
                )
        # Python 3.11 does not support tarfile's filter="data" argument.
        archive.extractall(destination, members=members)


def _extract_zip(filepath: Path, destination: Path) -> None:
    with zipfile.ZipFile(filepath) as archive:
        for member in archive.infolist():
            _validated_destination(destination, member.filename)
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(
                    f'Unsupported archive member type: {member.filename}'
                )
        archive.extractall(destination)


def _decompress_gzip(filepath: Path, destination: Path) -> None:
    # Strip a trailing .gz so the decompressed payload keeps its real name
    # (e.g. IGVFFI8835SMSP.tar.gz -> IGVFFI8835SMSP.tar). Some portal files
    # are double-gzipped, so the result may itself be another archive that
    # the nested-extraction loop handles.
    name = filepath.name
    output_name = name[:-3] if name.endswith('.gz') else name + '.decompressed'
    output_path = _validated_destination(destination, output_name)
    with gzip.open(filepath, 'rb') as source, open(output_path, 'wb') as target:
        shutil.copyfileobj(source, target)


def _extract(filepath: Path, destination: Path) -> None:
    """
    Extract a single archive into ``destination``.

    Format is detected by content, not extension. ``.tar``/``.tar.gz`` and
    ``.zip`` are unpacked fully; a plain gzip stream (including double-gzipped
    portal files) is decompressed one layer, leaving any inner archive for the
    nested-extraction loop.
    """
    if tarfile.is_tarfile(filepath):
        _extract_tar(filepath, destination)
    elif zipfile.is_zipfile(filepath):
        _extract_zip(filepath, destination)
    elif _is_gzip(filepath):
        _decompress_gzip(filepath, destination)
    else:
        raise ValueError(f'Unsupported archive format: {filepath}')


def _extract_nested_archives(directory: Path) -> None:
    while True:
        archives = [
            path for path in directory.rglob('*')
            if path.is_file() and _is_archive(path)
        ]
        if not archives:
            return
        for archive in archives:
            _extract(archive, archive.parent)
            # Remove the intermediate archive so only data files remain.
            archive.unlink()


def get_files_from_folder(filepath: str) -> Iterator[Path]:
    """
    Yield regular files from an archive or directory.

    For archives, extracts into a temporary directory (including nested and
    double-compressed archives) and keeps it available while iterating.
    Callers should open and process each file before moving to the next one.
    """
    path = Path(filepath)
    if path.is_dir():
        yield from sorted(p for p in path.rglob('*') if p.is_file())
        return
    if not path.is_file():
        raise FileNotFoundError(f'Input path does not exist: {filepath}')

    with tempfile.TemporaryDirectory(prefix='igvf-adapter-') as temp_directory:
        extracted_directory = Path(temp_directory)
        _extract(path, extracted_directory)
        _extract_nested_archives(extracted_directory)
        yield from sorted(
            p for p in extracted_directory.rglob('*') if p.is_file()
        )
