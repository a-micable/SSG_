"""
Tests for the site builder.
"""

from pathlib import Path

from ssg.builder import DependencyGraph, Paginator, SiteBuilder


class TestPaginator:
    """Regression tests for Paginator page counts."""

    def test_paginator_basic(self):
        """Test basic pagination."""
        items = list(range(25))
        paginator = Paginator(items, per_page=10)

        assert paginator.total_pages == 3

        page1 = paginator.page(1)
        assert len(page1) == 10
        assert page1[0] == 0

        page2 = paginator.page(2)
        assert len(page2) == 10
        assert page2[0] == 10

        page3 = paginator.page(3)
        assert len(page3) == 5
        assert page3[0] == 20

    def test_paginator_exact_division(self):
        """Exact division must not add an empty extra page."""
        items = list(range(20))
        paginator = Paginator(items, per_page=10)

        assert paginator.total_pages == 2

        page1 = paginator.page(1)
        assert len(page1) == 10

        page2 = paginator.page(2)
        assert len(page2) == 10

        page3 = paginator.page(3)
        assert len(page3) == 0

    def test_paginator_single_page(self):
        """Test pagination with items fitting on one page."""
        items = list(range(5))
        paginator = Paginator(items, per_page=10)

        assert paginator.total_pages == 1

        page1 = paginator.page(1)
        assert len(page1) == 5

    def test_paginator_empty(self):
        """Test pagination with no items."""
        paginator = Paginator([], per_page=10)

        assert paginator.total_pages == 1
        assert len(paginator.page(1)) == 0

    def test_has_prev(self):
        """Test has_prev method."""
        items = list(range(25))
        paginator = Paginator(items, per_page=10)

        assert not paginator.has_prev(1)
        assert paginator.has_prev(2)
        assert paginator.has_prev(3)

    def test_has_next(self):
        """Test has_next method."""
        items = list(range(25))
        paginator = Paginator(items, per_page=10)

        assert paginator.has_next(1)
        assert paginator.has_next(2)
        assert not paginator.has_next(3)


class TestDependencyGraph:
    """Test cases for DependencyGraph (includes BUG 2)."""

    def test_add_content_dependency(self):
        """Test adding content-template dependency."""
        graph = DependencyGraph()

        content_path = Path("content/post.md")
        template_path = Path("templates/post.html")

        graph.add_content_dependency(content_path, template_path)

        assert template_path in graph.content_to_templates[content_path]
        assert content_path in graph.template_to_content[template_path]

    def test_add_template_include(self):
        """Test adding template inclusion relationship."""
        graph = DependencyGraph()

        parent = Path("templates/post.html")
        included = Path("templates/base.html")

        graph.add_template_include(parent, included)

        assert included in graph.template_includes[parent]

    def test_get_affected_content_direct(self):
        """Test getting directly affected content."""
        graph = DependencyGraph()

        content1 = Path("content/post1.md")
        content2 = Path("content/post2.md")
        template = Path("templates/post.html")

        graph.add_content_dependency(content1, template)
        graph.add_content_dependency(content2, template)

        affected = graph.get_affected_content(template)

        assert content1 in affected
        assert content2 in affected

    def test_get_affected_content_transitive(self):
        """Test getting transitively affected content (BUG 2 case)."""
        graph = DependencyGraph()

        # Set up: post.html includes base.html, article.md uses post.html
        base_template = Path("templates/base.html")
        post_template = Path("templates/post.html")
        article = Path("content/article.md")

        graph.add_template_include(post_template, base_template)
        graph.add_content_dependency(article, post_template)

        affected = graph.get_affected_content(base_template)

        assert article in affected


class TestSiteBuilder:
    """Test cases for SiteBuilder."""

    def test_builder_initialization(self, sample_config):
        """Test builder initialization."""
        builder = SiteBuilder(sample_config)

        assert builder.config == sample_config
        assert builder.parser is not None
        assert builder.renderer is not None
        assert builder.asset_processor is not None

    def test_clean(self, sample_config):
        """Test cleaning output directory."""
        builder = SiteBuilder(sample_config)

        # Create output directory with some files
        sample_config.output_dir.mkdir(parents=True, exist_ok=True)
        test_file = sample_config.output_dir / "test.html"
        test_file.write_text("test")

        builder.clean()

        assert sample_config.output_dir.exists()
        assert not test_file.exists()

    def test_parse_content(self, sample_config):
        """Test content parsing."""
        builder = SiteBuilder(sample_config)
        builder.parse_content()

        # Should find 2 non-draft posts
        assert len(builder.parsed_content) == 2
        assert all(not item.is_draft for item in builder.parsed_content)

    def test_build_single_page(self, sample_config, temp_dir):
        """Test building a single page."""
        builder = SiteBuilder(sample_config)
        builder.parse_content()

        content = builder.parsed_content[0]
        output_path = sample_config.output_dir / content.slug / "index.html"

        builder.build_single_page(content, output_path)

        assert output_path.exists()
        html = output_path.read_text()
        assert content.title in html

    def test_build_content_pages(self, sample_config):
        """Test building all content pages."""
        builder = SiteBuilder(sample_config)
        builder.clean()
        builder.parse_content()
        builder.build_content_pages()

        # Check that output files exist
        for content in builder.parsed_content:
            output_path = sample_config.output_dir / content.slug / "index.html"
            assert output_path.exists()

    def test_build_index_pages(self, sample_config):
        """Test building index pages."""
        builder = SiteBuilder(sample_config)
        builder.clean()
        builder.parse_content()
        builder.build_index_pages()

        # Should have main index.html
        index_path = sample_config.output_dir / "index.html"
        assert index_path.exists()

    def test_build_tag_pages(self, sample_config):
        """Test building tag pages."""
        builder = SiteBuilder(sample_config)
        builder.clean()
        builder.parse_content()
        builder.build_tag_pages()

        # Check that tag pages exist
        python_tag_path = sample_config.output_dir / "tags" / "python" / "index.html"
        assert python_tag_path.exists()

    def test_full_build(self, sample_config):
        """Test complete build process."""
        builder = SiteBuilder(sample_config)
        builder.build()

        # Check various outputs
        assert (sample_config.output_dir / "index.html").exists()
        assert (sample_config.output_dir / "feed.xml").exists()
        assert (sample_config.output_dir / "sitemap.xml").exists()

        # Check content pages
        for content in builder.parsed_content:
            output_path = sample_config.output_dir / content.slug / "index.html"
            assert output_path.exists()
