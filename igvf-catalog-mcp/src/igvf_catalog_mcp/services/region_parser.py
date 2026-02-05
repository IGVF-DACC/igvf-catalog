"""Genomic region parser with flexible format support."""

import re
from typing import NamedTuple


class GenomicRegion(NamedTuple):
    """Parsed genomic region."""

    chromosome: str
    start: int
    end: int

    def __str__(self) -> str:
        """Format as chr:start-end."""
        return f'{self.chromosome}:{self.start}-{self.end}'


class RegionParser:
    """Parse and normalize genomic region formats."""

    # Valid chromosome names
    VALID_CHROMOSOMES = {
        'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10',
        'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19', 'chr20',
        'chr21', 'chr22', 'chrX', 'chrx', 'chrY', 'chry', 'chrM', 'chrm',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
        '21', '22', 'X', 'x', 'Y', 'y', 'M', 'm',
    }

    @classmethod
    def parse_region(cls, region: str) -> GenomicRegion:
        """
        Parse a genomic region string into structured components.

        Supports flexible formats:
        - chr1:1000000-2000000
        - 1:1000000-2000000
        - chr1:1,000,000-2,000,000 (commas)
        - chrX:1M-2M (M notation for millions)
        - chrX:1.5M-2.5M (decimal M notation)

        Args:
            region: Region string to parse

        Returns:
            GenomicRegion with normalized chromosome, start, and end

        Raises:
            ValueError: If region format is invalid
        """
        # Remove whitespace
        region = region.strip()

        # Basic format: chr:start-end
        match = re.match(
            r'^(chr)?([0-9]{1,2}|[XYM]):([\d,\.]+[KMG]?)-([\d,\.]+[KMG]?)$', region, re.IGNORECASE)

        if not match:
            raise ValueError(
                f"Invalid region format: '{region}'. "
                f"Expected format: 'chr1:1000-2000' or '1:1000-2000'. "
                f'The colon separates chromosome from position range.'
            )

        chr_prefix, chr_name, start_str, end_str = match.groups()

        # Normalize chromosome name
        chromosome = cls._normalize_chromosome(
            chr_name, chr_prefix is not None)

        # Parse positions with support for notations
        start = cls._parse_position(start_str)
        end = cls._parse_position(end_str)

        # Validate positions
        if start >= end:
            raise ValueError(
                f'Invalid region: start position ({start}) must be less than end position ({end})'
            )

        if start < 0:
            raise ValueError(
                f'Invalid region: start position ({start}) cannot be negative')

        return GenomicRegion(chromosome=chromosome, start=start, end=end)

    @classmethod
    def _normalize_chromosome(cls, chr_name: str, has_prefix: bool) -> str:
        """
        Normalize chromosome name to 'chrN' format.

        Args:
            chr_name: Chromosome name or number
            has_prefix: Whether the input already had 'chr' prefix

        Returns:
            Normalized chromosome name with 'chr' prefix
        """
        # Convert to lowercase for comparison
        chr_lower = chr_name.lower()

        # Normalize to uppercase for X, Y, M
        if chr_lower in ('x', 'y', 'm'):
            chr_name = chr_lower.upper()

        # Add chr prefix if not present
        if not has_prefix:
            return f'chr{chr_name}'

        return f'chr{chr_name}'

    @classmethod
    def _parse_position(cls, position_str: str) -> int:
        """
        Parse a position string, handling commas and K/M/G notation.

        Args:
            position_str: Position string (e.g., "1000000", "1,000,000", "1M", "1.5M")

        Returns:
            Position as integer

        Raises:
            ValueError: If position format is invalid
        """
        # Remove commas
        position_str = position_str.replace(',', '')

        # Check for K/M/G suffix
        multiplier = 1
        if position_str.upper().endswith('K'):
            multiplier = 1000
            position_str = position_str[:-1]
        elif position_str.upper().endswith('M'):
            multiplier = 1_000_000
            position_str = position_str[:-1]
        elif position_str.upper().endswith('G'):
            multiplier = 1_000_000_000
            position_str = position_str[:-1]

        try:
            # Support decimal notation (e.g., 1.5M)
            if '.' in position_str:
                position = int(float(position_str) * multiplier)
            else:
                position = int(position_str) * multiplier
        except ValueError:
            raise ValueError(f"Invalid position format: '{position_str}'")

        return position

    @classmethod
    def validate_region_size(cls, region: GenomicRegion, max_size: int) -> None:
        """
        Validate that a region is not too large.

        Args:
            region: The genomic region to validate
            max_size: Maximum allowed size in base pairs

        Raises:
            ValueError: If region is too large
        """
        size = region.end - region.start
        if size > max_size:
            raise ValueError(
                f'Region size ({size:,} bp) exceeds maximum allowed size ({max_size:,} bp)'
            )
