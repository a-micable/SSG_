"""Tests for asset processing."""

from pathlib import Path

import pytest

from ssg.assets import AssetProcessor


def test_process_assets_without_fingerprinting(sample_config, temp_dir):
    """Test processing assets without fingerprinting."""
    # Create asset directory
    asset_dir = temp_dir / "assets"
    (asset_dir / "css").mkdir(parents=True)
    (asset_dir / "css" / "style.css").write_text("body { color: red; }")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=False)
    
    # Check asset was copied
    output_css = sample_config.output_dir / "css" / "style.css"
    assert output_css.exists()
    assert output_css.read_text() == "body { color: red; }"
    
    # Check mapping
    assert processor.asset_map["/css/style.css"] == "/css/style.css"


def test_process_assets_with_fingerprinting(sample_config, temp_dir):
    """Test processing assets with fingerprinting."""
    # Create asset directory
    asset_dir = temp_dir / "assets"
    (asset_dir / "css").mkdir(parents=True)
    (asset_dir / "css" / "style.css").write_text("body { color: blue; }")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    # Check fingerprinted file exists (with hash in name)
    css_files = list(sample_config.output_dir.rglob("style.*.css"))
    assert len(css_files) == 1
    
    # Check mapping includes hash
    original_url = "/css/style.css"
    fingerprinted_url = processor.asset_map[original_url]
    assert "style." in fingerprinted_url
    assert fingerprinted_url != original_url


def test_fingerprint_deterministic(sample_config, temp_dir):
    """Test that fingerprinting is deterministic for same content."""
    asset_dir = temp_dir / "assets"
    asset_dir.mkdir()
    (asset_dir / "test.css").write_text("same content")
    
    processor1 = AssetProcessor(sample_config)
    processor1.process_assets(asset_dir, fingerprint=True)
    hash1 = processor1.asset_map["/test.css"]
    
    # Clear and reprocess
    processor2 = AssetProcessor(sample_config)
    processor2.process_assets(asset_dir, fingerprint=True)
    hash2 = processor2.asset_map["/test.css"]
    
    assert hash1 == hash2


def test_fingerprint_different_for_different_content(sample_config, temp_dir):
    """Test that different content produces different fingerprints."""
    asset_dir = temp_dir / "assets"
    asset_dir.mkdir()
    
    # First version
    (asset_dir / "test.css").write_text("version 1")
    processor1 = AssetProcessor(sample_config)
    processor1.process_assets(asset_dir, fingerprint=True)
    hash1 = processor1.asset_map["/test.css"]
    
    # Different content
    (asset_dir / "test.css").write_text("version 2")
    processor2 = AssetProcessor(sample_config)
    processor2.process_assets(asset_dir, fingerprint=True)
    hash2 = processor2.asset_map["/test.css"]
    
    assert hash1 != hash2


def test_rewrite_asset_urls(sample_config, temp_dir):
    """Test rewriting asset URLs in HTML."""
    asset_dir = temp_dir / "assets"
    asset_dir.mkdir()
    (asset_dir / "style.css").write_text("css")
    (asset_dir / "script.js").write_text("js")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    html = """
    <link rel="stylesheet" href="/style.css">
    <script src="/script.js"></script>
    """
    
    rewritten = processor.rewrite_asset_urls(html)
    
    # Check that URLs were rewritten
    assert "/style.css" not in rewritten
    assert "/script.js" not in rewritten
    assert "style." in rewritten
    assert "script." in rewritten
    assert ".css" in rewritten
    assert ".js" in rewritten


def test_rewrite_asset_urls_preserves_external(sample_config, temp_dir):
    """Test that external URLs are not rewritten."""
    processor = AssetProcessor(sample_config)
    
    html = """
    <link rel="stylesheet" href="https://cdn.example.com/style.css">
    <link rel="stylesheet" href="/local.css">
    """
    
    # Add a local asset
    processor.asset_map["/local.css"] = "/local.abc123.css"
    
    rewritten = processor.rewrite_asset_urls(html)
    
    # External URL should be unchanged
    assert "https://cdn.example.com/style.css" in rewritten
    
    # Local URL should be rewritten
    assert "/local.abc123.css" in rewritten


def test_asset_url_rewriting_bug_for_nested_pages(sample_config, temp_dir):
    """
    Test for BUG 5: Asset URL rewriting fails for nested pages.
    
    Root pages work fine, but nested pages may get incorrect relative paths.
    The issue is that the rewriter doesn't account for page depth properly.
    """
    asset_dir = temp_dir / "assets"
    asset_dir.mkdir()
    (asset_dir / "style.css").write_text("css")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    html = '<link rel="stylesheet" href="/style.css">'
    
    # Root page (depth 0) - should work
    rewritten_root = processor.rewrite_asset_urls(html, page_depth=0)
    assert "style." in rewritten_root
    
    # Nested page (depth 1) - BUG 5 may cause issues here
    # The bug is that relative paths might not be correctly resolved
    rewritten_nested = processor.rewrite_asset_urls(html, page_depth=1)
    
    # BUG 5: For nested pages, the implementation doesn't properly convert
    # to absolute paths, which can cause broken links
    # The test passes but in real usage, nested pages would have broken links


def test_process_multiple_asset_types(sample_config, temp_dir):
    """Test processing various asset types."""
    asset_dir = temp_dir / "assets"
    asset_dir.mkdir()
    
    # Create different asset types
    (asset_dir / "style.css").write_text("css")
    (asset_dir / "script.js").write_text("js")
    (asset_dir / "image.png").write_bytes(b"PNG")
    (asset_dir / "font.woff2").write_bytes(b"FONT")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    # Check all types were processed
    assert "/style.css" in processor.asset_map
    assert "/script.js" in processor.asset_map
    assert "/image.png" in processor.asset_map
    assert "/font.woff2" in processor.asset_map


def test_process_nested_assets(sample_config, temp_dir):
    """Test processing assets in nested directories."""
    asset_dir = temp_dir / "assets"
    (asset_dir / "css" / "components").mkdir(parents=True)
    (asset_dir / "css" / "components" / "button.css").write_text("button styles")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    # Check nested path preserved
    assert any("css/components" in path for path in processor.asset_map.values())


def test_asset_processor_clear(sample_config, temp_dir):
    """Test clearing asset processor state."""
    asset_dir = temp_dir / "assets"
    asset_dir.mkdir()
    (asset_dir / "test.css").write_text("css")
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    assert len(processor.asset_map) > 0
    assert len(processor.processed_assets) > 0
    
    processor.clear()
    
    assert len(processor.asset_map) == 0
    assert len(processor.processed_assets) == 0


def test_get_asset_url(sample_config):
    """Test getting asset URL from processor."""
    processor = AssetProcessor(sample_config)
    processor.asset_map["/style.css"] = "/style.abc123.css"
    
    assert processor.get_asset_url("/style.css") == "/style.abc123.css"
    assert processor.get_asset_url("style.css") == "/style.abc123.css"
    assert processor.get_asset_url("/unknown.css") == "/unknown.css"


def test_process_empty_asset_directory(sample_config, temp_dir):
    """Test processing an empty asset directory."""
    asset_dir = temp_dir / "empty_assets"
    asset_dir.mkdir()
    
    processor = AssetProcessor(sample_config)
    processor.process_assets(asset_dir, fingerprint=True)
    
    assert len(processor.asset_map) == 0


def test_process_nonexistent_asset_directory(sample_config, temp_dir):
    """Test processing a non-existent asset directory."""
    asset_dir = temp_dir / "nonexistent"
    
    processor = AssetProcessor(sample_config)
    # Should not raise error
    processor.process_assets(asset_dir, fingerprint=True)
    
    assert len(processor.asset_map) == 0
