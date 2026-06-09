"""
XML sitemap generation for SEO.
Generates sitemaps compliant with the sitemap protocol.
"""

from datetime import datetime
from pathlib import Path
from typing import List
from xml.etree.ElementTree import Element, SubElement, ElementTree
from .config import SiteConfig
from .parser import ParsedContent


class SitemapError(Exception):
    """Raised when sitemap generation fails."""
    pass


class SitemapGenerator:
    """Generates XML sitemaps for search engines."""
    
    SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
    
    def __init__(self, config: SiteConfig):
        """
        Initialize the sitemap generator.
        
        Args:
            config: Site configuration
        """
        self.config = config
    
    def _format_w3c_date(self, date_str: str) -> str:
        """
        Format date as W3C datetime (sitemap requirement).
        
        Args:
            date_str: Date string in ISO format
            
        Returns:
            W3C formatted date string (YYYY-MM-DD)
        """
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            # Try parsing with common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d"]:
                try:
                    date = datetime.strptime(date_str, fmt)
                    return date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # Fallback to today
            return datetime.now().strftime("%Y-%m-%d")
    
    def _create_url_element(self, url: str, lastmod: str, priority: str = "0.5") -> Element:
        """
        Create a sitemap URL element.
        
        Args:
            url: Full URL
            lastmod: Last modification date
            priority: Priority (0.0 to 1.0)
            
        Returns:
            XML Element for sitemap URL
        """
        url_elem = Element('url')
        
        # Location
        loc = SubElement(url_elem, 'loc')
        loc.text = url
        
        # Last modified
        lastmod_elem = SubElement(url_elem, 'lastmod')
        lastmod_elem.text = lastmod
        
        # Priority
        priority_elem = SubElement(url_elem, 'priority')
        priority_elem.text = priority
        
        return url_elem
    
    def generate(self, content_items: List[ParsedContent]):
        """
        Generate XML sitemap for content items.
        
        Args:
            content_items: List of content to include in sitemap
        """
        # Create urlset root element with namespace
        urlset = Element('urlset')
        urlset.set('xmlns', self.SITEMAP_NS)
        
        # Add homepage
        base_url = self.config.base_url.rstrip('/')
        homepage = self._create_url_element(
            base_url + "/",
            datetime.now().strftime("%Y-%m-%d"),
            "1.0"
        )
        urlset.append(homepage)
        
        # Add content pages
        for content in content_items:
            if not content.is_draft:
                full_url = f"{base_url}{content.url}"
                lastmod = self._format_w3c_date(content.date)
                
                url_elem = self._create_url_element(full_url, lastmod, "0.8")
                urlset.append(url_elem)
        
        # Write to file
        output_path = self.config.output_dir / "sitemap.xml"
        tree = ElementTree(urlset)
        
        # Pretty print
        self._indent(urlset)
        
        tree.write(
            output_path,
            encoding='utf-8',
            xml_declaration=True,
            method='xml'
        )
        
        print(f"  Generated sitemap with {len(urlset.findall('url'))} URLs")
    
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
