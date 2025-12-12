"""
RSS feed generation for SSG.

Generates valid RSS 2.0 feeds with proper timezone handling.
"""

import logging
from datetime import datetime, timezone
from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring

from ssg.config import SiteConfig
from ssg.parser import ParsedContent

logger = logging.getLogger(__name__)


class FeedGenerator:
    """
    Generates RSS 2.0 feeds for site content.
    
    Handles:
    - Valid RSS 2.0 XML generation
    - RFC 822 date formatting
    - Timezone conversion (BUG 4 location)
    """

    def __init__(self, config: SiteConfig) -> None:
        """
        Initialize feed generator.
        
        Args:
            config: Site configuration
        """
        self.config = config

    def generate(self, posts: List[ParsedContent], max_items: int = 20) -> str:
        """
        Generate RSS feed XML.
        
        Args:
            posts: List of content items to include
            max_items: Maximum number of items to include
            
        Returns:
            RSS 2.0 XML as string
        """
        # Create root RSS element
        rss = Element("rss")
        rss.set("version", "2.0")
        rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

        channel = SubElement(rss, "channel")

        # Channel metadata
        SubElement(channel, "title").text = self.config.site_name
        SubElement(channel, "link").text = self.config.base_url
        SubElement(channel, "description").text = (
            self.config.description or f"Latest posts from {self.config.site_name}"
        )
        SubElement(channel, "language").text = self.config.language

        # Self link (atom requirement)
        atom_link = SubElement(channel, "atom:link")
        atom_link.set("href", f"{self.config.base_url}/rss.xml")
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")

        # Add items (posts)
        for post in posts[:max_items]:
            self._add_item(channel, post)

        # Convert to XML string with declaration
        xml_bytes = tostring(rss, encoding="utf-8", method="xml")
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes.decode("utf-8")

        return xml_str

    def _add_item(self, channel: Element, post: ParsedContent) -> None:
        """
        Add a single item to the RSS feed.
        
        Args:
            channel: RSS channel element
            post: Content to add as item
        """
        item = SubElement(channel, "item")

        # Required fields
        SubElement(item, "title").text = post.metadata.title
        SubElement(item, "link").text = self.config.base_url + post.url_path
        SubElement(item, "guid").text = self.config.base_url + post.url_path

        # Description (use metadata description or truncated content)
        description = post.metadata.description
        if not description:
            # Use first 200 chars of content as description
            description = post.html[:200].strip()
            if len(post.html) > 200:
                description += "..."
        SubElement(item, "description").text = description

        # Publication date
        if post.metadata.date:
            pub_date = self._format_rfc822_date(post.metadata.date)
            if pub_date:
                SubElement(item, "pubDate").text = pub_date

        # Author
        author = post.metadata.author or self.config.author
        if author:
            # RSS 2.0 author format: email (name)
            # We'll just use name since we don't have email
            SubElement(item, "author").text = author

        # Categories (tags)
        for tag in post.metadata.tags:
            SubElement(item, "category").text = tag

    def _format_rfc822_date(self, date_value: str) -> str:
        """
        Format a date string as RFC 822 (RSS date format).
        
        BUG 4: This doesn't properly convert to UTC.
        Dates are emitted in local system time instead of UTC,
        which causes feed validators to fail or produce incorrect times.
        
        Args:
            date_value: Date string from content metadata
            
        Returns:
            RFC 822 formatted date string, or empty string if parsing fails
        """
        try:
            # Parse the date string (assuming ISO format like 2024-03-15)
            if isinstance(date_value, str):
                # Try to parse common formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Couldn't parse
                    logger.warning(f"Could not parse date: {date_value}")
                    return ""
            else:
                dt = date_value

            # BUG 4: This is where the timezone bug exists
            # We should convert to UTC, but instead we're using local time
            # The correct approach would be:
            # 1. Assume the parsed datetime is in the configured timezone
            # 2. Convert to UTC
            # 3. Format as RFC 822 with UTC timezone
            
            # Current buggy implementation: just format as-is
            # This will use local system timezone, not UTC
            rfc822_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # BUG 4 NOTE: The "+0000" claims this is UTC, but dt might not be UTC
            # This causes incorrect timestamps in the feed
            
            return rfc822_date

        except Exception as e:
            logger.warning(f"Failed to format date {date_value}: {e}")
            return ""
