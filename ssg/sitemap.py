"""
XML sitemap generation for SSG.

Generates valid XML sitemaps for search engines.
"""

import logging
from datetime import datetime
from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring

from ssg.config import SiteConfig
from ssg.parser import ParsedContent

logger = logging.getLogger(__name__)


class SitemapGenerator:
    """
    Generates XML sitemaps compliant with sitemap protocol.
    
    Handles:
    - Valid XML sitemap generation
    - URL normalization
    - Change frequency and priority hints
    """

    def __init__(self, config: SiteConfig) -> None:
        """
        Initialize sitemap generator.
        
        Args:
            config: Site configuration
        """
        self.config = config

    def generate(self, content: List[ParsedContent]) -> str:
        """
        Generate XML sitemap.
        
        Args:
            content: List of content items to include
            
        Returns:
            XML sitemap as string
        """
        # Create root urlset element
        urlset = Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        # Add home page
        self._add_url(urlset, "/", priority="1.0", changefreq="daily")

        # Add all content pages
        for item in content:
            if not item.metadata.draft:
                self._add_url(
                    urlset,
                    item.url_path,
                    lastmod=item.metadata.date,
                    priority="0.8",
                    changefreq="weekly",
                )

        # Convert to XML string with declaration
        xml_bytes = tostring(urlset, encoding="utf-8", method="xml")
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes.decode("utf-8")

        return xml_str

    def _add_url(
        self,
        urlset: Element,
        path: str,
        lastmod: str = None,
        changefreq: str = None,
        priority: str = None,
    ) -> None:
        """
        Add a URL entry to the sitemap.
        
        Args:
            urlset: XML urlset element
            path: URL path
            lastmod: Last modification date (ISO format)
            changefreq: Change frequency hint
            priority: Priority hint (0.0-1.0)
        """
        url = SubElement(urlset, "url")

        # Location (required)
        loc = self.config.base_url + path
        SubElement(url, "loc").text = loc

        # Last modification date (optional)
        if lastmod:
            try:
                # Format as YYYY-MM-DD
                if isinstance(lastmod, str):
                    # Try to parse and reformat
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            dt = datetime.strptime(lastmod, fmt)
                            SubElement(url, "lastmod").text = dt.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                elif isinstance(lastmod, datetime):
                    SubElement(url, "lastmod").text = lastmod.strftime("%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Failed to format lastmod date {lastmod}: {e}")

        # Change frequency (optional)
        if changefreq:
            SubElement(url, "changefreq").text = changefreq

        # Priority (optional)
        if priority:
            SubElement(url, "priority").text = priority
