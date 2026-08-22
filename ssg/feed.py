"""
RSS feed generation for blog posts.
Generates RSS 2.0 compliant feeds.
"""

from datetime import datetime
from pathlib import Path
from typing import List
from xml.etree.ElementTree import Element, SubElement, ElementTree
from .config import SiteConfig
from .parser import ParsedContent


class FeedError(Exception):
    """Raised when feed generation fails."""

    pass


class FeedGenerator:
    """
    Generates RSS 2.0 feeds.

    BUG 4 LOCATION: Timezone handling - dates are emitted in local time instead of UTC.
    """

    def __init__(self, config: SiteConfig):
        """
        Initialize the feed generator.

        Args:
            config: Site configuration
        """
        self.config = config

    def _format_rfc822_date(self, date_str: str) -> str:
        """
        Format date as RFC 822 (RSS 2.0 requirement).

        BUG 4: Uses local system timezone instead of UTC.
        RSS spec requires dates in GMT, but this outputs local time.

        Example:
            Input: "2024-03-15"
            Expected: "Fri, 15 Mar 2024 00:00:00 GMT"
            Actual: "Fri, 15 Mar 2024 00:00:00 PST" (or whatever local TZ)

        This causes feed validators to fail or show incorrect times.

        Args:
            date_str: Date string in ISO format

        Returns:
            RFC 822 formatted date string
        """
        if not isinstance(date_str, str):
            date_str = str(date_str)
        try:
            # Parse ISO date
            date = datetime.fromisoformat(date_str)
        except (ValueError, AttributeError):
            # Try parsing with common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d"]:
                try:
                    date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                # Fallback to current time
                date = datetime.now()

        # BUG 4: Should convert to UTC before formatting
        # Should use: date.astimezone(timezone.utc).strftime(...)
        # Instead, uses local time:
        return date.strftime("%a, %d %b %Y %H:%M:%S %z")
        # This outputs local timezone offset, not GMT

    def _create_item_element(self, content: ParsedContent) -> Element:
        """
        Create an RSS item element for content.

        Args:
            content: Content to convert to RSS item

        Returns:
            XML Element for RSS item
        """
        item = Element("item")

        # Title
        title = SubElement(item, "title")
        title.text = content.title

        # Link
        link = SubElement(item, "link")
        full_url = f"{self.config.base_url.rstrip('/')}{content.url}"
        link.text = full_url

        # Description (use content as description)
        description = SubElement(item, "description")
        description.text = content.content

        # Publication date (BUG 4: Uses local time instead of UTC)
        pub_date = SubElement(item, "pubDate")
        pub_date.text = self._format_rfc822_date(content.date)

        # GUID
        guid = SubElement(item, "guid")
        guid.text = full_url
        guid.set("isPermaLink", "true")

        # Categories (tags)
        for tag in content.tags:
            category = SubElement(item, "category")
            category.text = tag

        return item

    def generate(self, content_items: List[ParsedContent], max_items: int = 20):
        """
        Generate RSS feed for content items.

        Args:
            content_items: List of content to include in feed
            max_items: Maximum number of items to include
        """
        # Create RSS root element
        rss = Element("rss")
        rss.set("version", "2.0")

        # Create channel
        channel = SubElement(rss, "channel")

        # Channel metadata
        title = SubElement(channel, "title")
        title.text = self.config.site_name

        link = SubElement(channel, "link")
        link.text = self.config.base_url

        description = SubElement(channel, "description")
        description.text = self.config.description or f"Feed for {self.config.site_name}"

        language = SubElement(channel, "language")
        language.text = self.config.language

        # Last build date (BUG 4: Also uses local time)
        last_build = SubElement(channel, "lastBuildDate")
        last_build.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        # Add items (most recent first, limited to max_items)
        for content in content_items[:max_items]:
            if not content.is_draft:
                item = self._create_item_element(content)
                channel.append(item)

        # Write to file
        output_path = self.config.output_dir / "feed.xml"
        tree = ElementTree(rss)

        # Pretty print
        self._indent(rss)

        tree.write(output_path, encoding="utf-8", xml_declaration=True, method="xml")

        print(f"  Generated RSS feed with {len(channel.findall('item'))} items")

    def _indent(self, elem: Element, level: int = 0):
        """
        Add pretty-printing indentation to XML.

        Args:
            elem: XML element to indent
            level: Current indentation level
        """
        indent_str = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent_str + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent_str
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent_str
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent_str
