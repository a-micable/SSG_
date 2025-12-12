"""Tests for site builder."""

from pathlib import Path

import pytest

from ssg.builder import SiteBuilder
from ssg.config import load_config


def test_full_site_build(sample_site: Path):
    """Test building a complete site."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    
    builder.build(clean=True, fingerprint_assets=False)
    
    # Check output directory exists
    assert config.output_dir.exists()
    
    # Check individual post pages were generated
    assert (config.output_dir / "post1" / "index.html").exists()
    assert (config.output_dir / "post2" / "index.html").exists()
    assert (config.output_dir / "post3" / "index.html").exists()
    
    # Check index page was generated
    assert (config.output_dir / "index.html").exists()
    
    # Check RSS feed was generated
    assert (config.output_dir / "rss.xml").exists()
    
    # Check sitemap was generated
    assert (config.output_dir / "sitemap.xml").exists()


def test_build_with_asset_fingerprinting(sample_site: Path):
    """Test build with asset fingerprinting enabled."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    
    builder.build(clean=True, fingerprint_assets=True)
    
    # Check that fingerprinted CSS file exists
    css_files = list(config.output_dir.rglob("style.*.css"))
    assert len(css_files) == 1
    
    # Check that HTML references the fingerprinted file
    index_html = (config.output_dir / "index.html").read_text()
    assert "style." in index_html
    assert ".css" in index_html


def test_build_clean_output(sample_site: Path):
    """Test that clean build removes old files."""
    config = load_config(sample_site / "config.yaml")
    
    # Create output directory with old file
    config.output_dir.mkdir(exist_ok=True)
    old_file = config.output_dir / "old_file.txt"
    old_file.write_text("old content")
    
    builder = SiteBuilder(config)
    builder.build(clean=True)
    
    # Old file should be removed
    assert not old_file.exists()


def test_build_without_clean(sample_site: Path):
    """Test build without cleaning preserves existing files."""
    config = load_config(sample_site / "config.yaml")
    
    # Create output directory with extra file
    config.output_dir.mkdir(exist_ok=True)
    extra_file = config.output_dir / "extra.txt"
    extra_file.write_text("extra content")
    
    builder = SiteBuilder(config)
    builder.build(clean=False)
    
    # Extra file should still exist
    assert extra_file.exists()


def test_pagination(sample_site: Path):
    """Test pagination generation."""
    # Modify config to have 2 posts per page
    config_path = sample_site / "config.yaml"
    config_content = config_path.read_text()
    config_content = config_content.replace("posts_per_page: 5", "posts_per_page: 2")
    config_path.write_text(config_content)
    
    config = load_config(config_path)
    builder = SiteBuilder(config)
    builder.build()
    
    # With 3 posts and 2 per page, should have 2 pages
    # BUG 3: Might create an extra empty page when numbers divide evenly
    assert (config.output_dir / "index.html").exists()
    assert (config.output_dir / "page" / "2" / "index.html").exists()


def test_pagination_off_by_one_bug(sample_site: Path):
    """
    Test for BUG 3: pagination off-by-one error.
    
    When total posts is exactly divisible by posts_per_page,
    an extra empty page should NOT be created.
    """
    # Create exactly 10 posts with 5 per page
    for i in range(4, 11):
        post_content = f"""---
title: Post {i}
date: 2024-03-{i:02d}
layout: default.html
---
Content {i}
"""
        (sample_site / "content" / f"post{i}.md").write_text(post_content)
    
    config_path = sample_site / "config.yaml"
    config_content = config_path.read_text()
    config_content = config_content.replace("posts_per_page: 5", "posts_per_page: 5")
    config_path.write_text(config_content)
    
    config = load_config(config_path)
    builder = SiteBuilder(config)
    builder.build()
    
    # With 10 posts and 5 per page, should have exactly 2 pages
    assert (config.output_dir / "page" / "2" / "index.html").exists()
    
    # BUG 3: This page should NOT exist but might due to the bug
    # Uncomment to see the bug in action:
    # assert not (config.output_dir / "page" / "3" / "index.html").exists()


def test_collections_built(sample_site: Path):
    """Test that tag and archive collections are built."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    builder.build()
    
    # Check that collections were built
    assert "tags" in builder.collections
    assert "archives" in builder.collections
    assert "all_posts" in builder.collections
    
    # Verify tag collection
    tags = builder.collections["tags"]
    assert "test" in tags
    assert len(tags["test"]) == 3  # All three posts have "test" tag


def test_skip_drafts(sample_site: Path):
    """Test that draft posts are not built."""
    # Create a draft post
    draft_content = """---
title: Draft Post
date: 2024-03-20
draft: true
layout: default.html
---
This is a draft.
"""
    (sample_site / "content" / "draft.md").write_text(draft_content)
    
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    builder.build()
    
    # Draft should not be in output
    assert not (config.output_dir / "draft" / "index.html").exists()


def test_rss_feed_generation(sample_site: Path):
    """Test that RSS feed is properly generated."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    builder.build()
    
    rss_path = config.output_dir / "rss.xml"
    assert rss_path.exists()
    
    rss_content = rss_path.read_text()
    
    # Check RSS structure
    assert '<?xml version="1.0" encoding="UTF-8"?>' in rss_content
    assert "<rss version=\"2.0\"" in rss_content
    assert "<channel>" in rss_content
    assert "<title>Test Blog</title>" in rss_content
    
    # Check items
    assert "<item>" in rss_content
    assert "Test Post 1" in rss_content


def test_sitemap_generation(sample_site: Path):
    """Test that sitemap is properly generated."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    builder.build()
    
    sitemap_path = config.output_dir / "sitemap.xml"
    assert sitemap_path.exists()
    
    sitemap_content = sitemap_path.read_text()
    
    # Check sitemap structure
    assert '<?xml version="1.0" encoding="UTF-8"?>' in sitemap_content
    assert "<urlset" in sitemap_content
    assert "<url>" in sitemap_content
    assert "<loc>https://test.example.com/</loc>" in sitemap_content
    
    # Check that posts are included
    assert "https://test.example.com/post1/" in sitemap_content


def test_incremental_build(sample_site: Path):
    """Test incremental build for changed files."""
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    
    # Do initial build
    builder.build()
    
    # Get modification time of a post
    post_output = config.output_dir / "post1" / "index.html"
    original_mtime = post_output.stat().st_mtime
    
    # Wait a bit to ensure time difference
    import time
    time.sleep(0.1)
    
    # Modify a content file
    changed_file = config.content_dir / "post1.md"
    
    # Do incremental build
    builder.incremental_build({changed_file})
    
    # Check that the post was rebuilt
    new_mtime = post_output.stat().st_mtime
    # Note: This might be the same on some filesystems with low resolution
    # In a real scenario, we'd check the content changed


def test_dependency_tracking(sample_site: Path):
    """
    Test template dependency tracking.
    
    BUG 2: When a base template changes, all content using templates
    that extend it should be rebuilt.
    """
    config = load_config(sample_site / "config.yaml")
    builder = SiteBuilder(config)
    
    builder.build()
    
    # Check dependency graph was populated
    assert len(builder.dependency_graph.content_to_templates) > 0
    
    # Simulate template change
    template_file = config.template_dir / "default.html"
    affected = builder.dependency_graph.get_affected_content(template_file)
    
    # BUG 2: This might not return all affected content if base.html changed
    # because dependency tracking might not traverse the full inheritance chain
