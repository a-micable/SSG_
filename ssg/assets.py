"""
Asset processing for SSG.

Handles copying static assets and asset fingerprinting for cache busting.
Tracks asset mappings for URL rewriting in HTML.
"""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Dict, Set

from ssg import BuildError
from ssg.config import SiteConfig

logger = logging.getLogger(__name__)


class AssetProcessor:
    """
    Processes static assets with optional fingerprinting.
    
    Handles:
    - Copying assets from source to output directory
    - Content-based fingerprinting for cache busting
    - Tracking asset URL mappings for rewriting
    """

    def __init__(self, config: SiteConfig) -> None:
        """
        Initialize asset processor.
        
        Args:
            config: Site configuration
        """
        self.config = config
        self.asset_map: Dict[str, str] = {}  # Original path -> Fingerprinted path
        self.processed_assets: Set[Path] = set()

    def process_assets(self, asset_dir: Path, fingerprint: bool = True) -> None:
        """
        Process all assets in a directory.
        
        Args:
            asset_dir: Directory containing static assets
            fingerprint: Whether to apply content fingerprinting
            
        Raises:
            BuildError: If asset processing fails
        """
        if not asset_dir.exists():
            logger.info(f"Asset directory not found: {asset_dir}, skipping")
            return

        logger.info(f"Processing assets from {asset_dir}")

        # Discover all asset files
        asset_files = self._discover_assets(asset_dir)

        for asset_file in asset_files:
            self._process_single_asset(asset_file, asset_dir, fingerprint)

        logger.info(f"Processed {len(asset_files)} assets")

    def _discover_assets(self, asset_dir: Path) -> list[Path]:
        """
        Discover all asset files in a directory.
        
        Args:
            asset_dir: Root asset directory
            
        Returns:
            List of asset file paths
        """
        assets = []
        
        # Common asset patterns
        patterns = ["**/*.css", "**/*.js", "**/*.jpg", "**/*.jpeg", "**/*.png", 
                   "**/*.gif", "**/*.svg", "**/*.woff", "**/*.woff2", "**/*.ttf",
                   "**/*.eot", "**/*.ico", "**/*.webp", "**/*.mp4", "**/*.webm"]
        
        for pattern in patterns:
            for file_path in asset_dir.glob(pattern):
                if file_path.is_file():
                    assets.append(file_path)
        
        return sorted(set(assets))  # Remove duplicates and sort

    def _process_single_asset(
        self, asset_file: Path, asset_dir: Path, fingerprint: bool
    ) -> None:
        """
        Process a single asset file.
        
        Args:
            asset_file: Path to asset file
            asset_dir: Root asset directory
            fingerprint: Whether to apply fingerprinting
        """
        try:
            # Calculate relative path from asset_dir
            rel_path = asset_file.relative_to(asset_dir)
            
            if fingerprint:
                # Generate content hash
                content_hash = self._hash_file(asset_file)
                
                # Create fingerprinted filename
                stem = asset_file.stem
                suffix = asset_file.suffix
                fingerprinted_name = f"{stem}.{content_hash[:8]}{suffix}"
                
                # Build output path with fingerprint
                output_path = self.config.output_dir / rel_path.parent / fingerprinted_name
                
                # Store mapping for URL rewriting
                original_url = "/" + str(rel_path).replace("\\", "/")
                fingerprinted_url = "/" + str(rel_path.parent / fingerprinted_name).replace("\\", "/")
                self.asset_map[original_url] = fingerprinted_url
            else:
                # No fingerprinting, just copy
                output_path = self.config.output_dir / rel_path
                original_url = "/" + str(rel_path).replace("\\", "/")
                self.asset_map[original_url] = original_url

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(asset_file, output_path)
            self.processed_assets.add(asset_file)
            
            logger.debug(f"Processed asset: {asset_file} -> {output_path}")
            
        except Exception as e:
            raise BuildError(f"Failed to process asset {asset_file}: {e}")

    def _hash_file(self, file_path: Path) -> str:
        """
        Generate content hash for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of file content hash
        """
        hasher = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()

    def rewrite_asset_urls(self, html: str, page_depth: int = 0) -> str:
        """
        Rewrite asset URLs in HTML to use fingerprinted versions.
        
        BUG 5: This has a bug with relative path resolution for nested pages.
        Root pages work fine, but nested pages may generate incorrect relative paths.
        
        Args:
            html: HTML content with asset references
            page_depth: Depth of page in site hierarchy (for relative path calculation)
            
        Returns:
            HTML with rewritten asset URLs
        """
        result = html
        
        for original_url, fingerprinted_url in self.asset_map.items():
            # BUG 5: This simple replacement doesn't account for page depth
            # For nested pages, relative paths like ../style.css may break
            # Should convert all asset paths to absolute paths from root
            
            # Replace various reference patterns
            # href="original" -> href="fingerprinted"
            result = result.replace(f'href="{original_url}"', f'href="{fingerprinted_url}"')
            result = result.replace(f"href='{original_url}'", f"href='{fingerprinted_url}'")
            
            # src="original" -> src="fingerprinted"
            result = result.replace(f'src="{original_url}"', f'src="{fingerprinted_url}"')
            result = result.replace(f"src='{original_url}'", f"src='{fingerprinted_url}'")
            
            # BUG 5 NOTE: For nested pages (page_depth > 0), we should be converting
            # to absolute paths, but this implementation doesn't do that correctly.
            # This will cause broken asset links on nested pages like /blog/post/index.html
        
        return result

    def get_asset_url(self, original_path: str) -> str:
        """
        Get the fingerprinted URL for an asset.
        
        Args:
            original_path: Original asset path
            
        Returns:
            Fingerprinted asset URL, or original if not found
        """
        # Normalize path
        if not original_path.startswith("/"):
            original_path = "/" + original_path
        
        return self.asset_map.get(original_path, original_path)

    def clear(self) -> None:
        """Clear all asset mappings and processed asset tracking."""
        self.asset_map.clear()
        self.processed_assets.clear()
