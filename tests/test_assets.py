"""
Tests for asset processing.
"""

import pytest
from pathlib import Path
from ssg.assets import AssetProcessor


class TestAssetProcessor:
    """Test cases for AssetProcessor (includes BUG 5)."""

    def test_compute_hash(self, sample_config, temp_dir):
        """Test file hash computation."""
        processor = AssetProcessor(sample_config)

        test_file = temp_dir / "test.css"
        test_file.write_text("body { margin: 0; }")

        hash1 = processor._compute_hash(test_file)
        assert len(hash1) == 8
        assert hash1.isalnum()

        # Same content should produce same hash
        hash2 = processor._compute_hash(test_file)
        assert hash1 == hash2

        # Different content should produce different hash
        test_file.write_text("body { padding: 0; }")
        hash3 = processor._compute_hash(test_file)
        assert hash1 != hash3

    def test_should_fingerprint(self, sample_config):
        """Test fingerprinting decision logic."""
        processor = AssetProcessor(sample_config)

        assert processor._should_fingerprint(Path("style.css"))
        assert processor._should_fingerprint(Path("script.js"))
        assert not processor._should_fingerprint(Path("image.png"))
        assert not processor._should_fingerprint(Path("font.woff"))

    def test_fingerprint_filename(self, sample_config):
        """Test fingerprinted filename generation."""
        processor = AssetProcessor(sample_config)

        result = processor._fingerprint_filename(Path("style.css"), "abc123")
        assert result == "style.abc123.css"

        result = processor._fingerprint_filename(Path("app.js"), "def456")
        assert result == "app.def456.js"

    def test_process_file_with_fingerprinting(self, sample_config, temp_dir):
        """Test processing a file that should be fingerprinted."""
        # Create asset
        asset_dir = temp_dir / "assets"
        asset_dir.mkdir(exist_ok=True)
        css_file = asset_dir / "style.css"
        css_file.write_text("body { margin: 0; }")

        processor = AssetProcessor(sample_config)
        output_path = processor.process_file(css_file, asset_dir)

        # Check output exists
        assert output_path.exists()

        # Check filename is fingerprinted
        assert ".css" in output_path.name
        assert output_path.stem != "style"  # Should have hash

        # Check mapping was created
        assert "/style.css" in processor.fingerprint_map

    def test_process_file_without_fingerprinting(self, sample_config, temp_dir):
        """Test processing a file that should not be fingerprinted."""
        # Create asset
        asset_dir = temp_dir / "assets"
        asset_dir.mkdir(exist_ok=True)
        image_file = asset_dir / "logo.png"
        image_file.write_bytes(b"fake image data")

        processor = AssetProcessor(sample_config)
        output_path = processor.process_file(image_file, asset_dir)

        # Check output exists
        assert output_path.exists()

        # Check filename is NOT fingerprinted
        assert output_path.name == "logo.png"

        # Check no mapping was created
        assert "/logo.png" not in processor.fingerprint_map

    def test_process_directory(self, sample_config):
        """Test processing entire asset directory."""
        processor = AssetProcessor(sample_config)
        processor.process_directory(sample_config.asset_dirs[0])

        # Check that CSS was processed
        output_css = sample_config.output_dir / "css" / "style.css"
        # Note: Filename will be fingerprinted, so exact name varies
        css_files = list((sample_config.output_dir / "css").glob("style.*.css"))
        assert len(css_files) > 0 or output_css.exists()

    def test_process_all_assets(self, sample_config):
        """Test processing all configured asset directories."""
        processor = AssetProcessor(sample_config)
        processor.process()

        # Check that assets were processed
        assert len(processor.fingerprint_map) > 0

    def test_rewrite_asset_urls(self, sample_config):
        """Test URL rewriting in HTML."""
        processor = AssetProcessor(sample_config)

        # Simulate fingerprint map
        processor.fingerprint_map = {
            "/style.css": "/style.abc123.css",
            "/app.js": "/app.def456.js",
        }

        html = """
        <link rel="stylesheet" href="/style.css">
        <script src="/app.js"></script>
        """

        result = processor.rewrite_asset_urls(html)

        assert "/style.abc123.css" in result
        assert "/app.def456.js" in result
        assert "/style.css" not in result
        assert "/app.js" not in result

    def test_rewrite_asset_urls_relative_paths(self, sample_config):
        """Test URL rewriting with relative paths (BUG 5 case)."""
        processor = AssetProcessor(sample_config)

        processor.fingerprint_map = {
            "/style.css": "/style.abc123.css",
        }

        html = '<link rel="stylesheet" href="../style.css">'

        result = processor.rewrite_asset_urls(html)

        assert "/style.abc123.css" in result
        assert "../style.css" not in result

    def test_get_fingerprinted_url(self, sample_config):
        """Test getting fingerprinted URL for an asset."""
        processor = AssetProcessor(sample_config)

        processor.fingerprint_map = {
            "/style.css": "/style.abc123.css",
        }

        result = processor.get_fingerprinted_url("/style.css")
        assert result == "/style.abc123.css"

        result = processor.get_fingerprinted_url("style.css")
        assert result == "/style.abc123.css"

        # Non-existent asset returns original
        result = processor.get_fingerprinted_url("/nonexistent.css")
        assert result == "/nonexistent.css"
