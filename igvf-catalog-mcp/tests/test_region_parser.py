"""Tests for region parser."""

import pytest
from igvf_catalog_mcp.services.region_parser import RegionParser, GenomicRegion


class TestRegionParser:
    """Test region parser functionality."""

    def test_parse_basic_region(self):
        """Test parsing of basic region format."""
        region = RegionParser.parse_region('chr1:1000-2000')
        assert region.chromosome == 'chr1'
        assert region.start == 1000
        assert region.end == 2000

    def test_parse_without_chr_prefix(self):
        """Test parsing region without 'chr' prefix."""
        region = RegionParser.parse_region('1:1000-2000')
        assert region.chromosome == 'chr1'
        assert region.start == 1000
        assert region.end == 2000

    def test_parse_with_commas(self):
        """Test parsing region with comma separators."""
        region = RegionParser.parse_region('chr1:1,000,000-2,000,000')
        assert region.chromosome == 'chr1'
        assert region.start == 1000000
        assert region.end == 2000000

    def test_parse_with_m_notation(self):
        """Test parsing region with M (million) notation."""
        region = RegionParser.parse_region('chr1:1M-2M')
        assert region.chromosome == 'chr1'
        assert region.start == 1000000
        assert region.end == 2000000

    def test_parse_with_decimal_m(self):
        """Test parsing region with decimal M notation."""
        region = RegionParser.parse_region('chr1:1.5M-2.5M')
        assert region.chromosome == 'chr1'
        assert region.start == 1500000
        assert region.end == 2500000

    def test_parse_with_k_notation(self):
        """Test parsing region with K (thousand) notation."""
        region = RegionParser.parse_region('chr1:1K-2K')
        assert region.chromosome == 'chr1'
        assert region.start == 1000
        assert region.end == 2000

    def test_parse_chrx(self):
        """Test parsing X chromosome."""
        region = RegionParser.parse_region('chrX:1000-2000')
        assert region.chromosome == 'chrX'

        region = RegionParser.parse_region('X:1000-2000')
        assert region.chromosome == 'chrX'

    def test_parse_chry(self):
        """Test parsing Y chromosome."""
        region = RegionParser.parse_region('chrY:1000-2000')
        assert region.chromosome == 'chrY'

        region = RegionParser.parse_region('y:1000-2000')
        assert region.chromosome == 'chrY'

    def test_parse_chrm(self):
        """Test parsing mitochondrial chromosome."""
        region = RegionParser.parse_region('chrM:1000-2000')
        assert region.chromosome == 'chrM'

    def test_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match='Invalid region format'):
            RegionParser.parse_region('chr1-1000-2000')

    def test_start_greater_than_end(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match='start position.*must be less than end'):
            RegionParser.parse_region('chr1:2000-1000')

    def test_negative_position(self):
        """Test that negative positions raise ValueError."""
        with pytest.raises(ValueError, match='cannot be negative'):
            RegionParser.parse_region('chr1:-1000-2000')

    def test_region_str_representation(self):
        """Test string representation of GenomicRegion."""
        region = GenomicRegion(chromosome='chr1', start=1000, end=2000)
        assert str(region) == 'chr1:1000-2000'

    def test_validate_region_size(self):
        """Test region size validation."""
        region = GenomicRegion(chromosome='chr1', start=0, end=10000)

        # Should not raise for size within limit
        RegionParser.validate_region_size(region, max_size=20000)

        # Should raise for size exceeding limit
        with pytest.raises(ValueError, match='exceeds maximum allowed size'):
            RegionParser.validate_region_size(region, max_size=5000)
