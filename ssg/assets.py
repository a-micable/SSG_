"""
Asset processing with fingerprinting and copying.
Handles static files like CSS, JS, and images.
"""

import hashlib
import shutil
from pathlib import Path
from typing import Dict, Set
from .config import SiteConfig


class AssetError(Exception):
    """Raised when asset processing fails."""

    pass


class AssetProcessor:
    """
    Processes static assets with optional fingerprinting.

    BUG 5 LOCATION: Path resolution for fingerprinted assets breaks on nested pages.
    """

    def __init__(self, config: SiteConfig):
        """
        Initialize the asset processor.

        Args:
            config: Site configuration
        """
        self.config = config
        self.fingerprint_map: Dict[str, str] = {}

    def _compute_hash(self, file_path: Path) -> str:
        """
        Compute MD5 hash of a file for fingerprinting.

        Args:
            file_path: Path to file

        Returns:
            First 8 characters of MD5 hash
        """
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()[:8]

    def _should_fingerprint(self, file_path: Path) -> bool:
        """
        Check if a file should be fingerprinted.

        Args:
            file_path: Path to file

        Returns:
            True if file should be fingerprinted
        """
        # Fingerprint CSS and JS files
        return file_path.suffix in [".css", ".js"]

    def _fingerprint_filename(self, file_path: Path, content_hash: str) -> str:
        """
        Generate fingerprinted filename.

        Args:
            file_path: Original file path
            content_hash: Content hash

        Returns:
            Fingerprinted filename (e.g., style.abc123.css)
        """
        stem = file_path.stem
        suffix = file_path.suffix
        return f"{stem}.{content_hash}{suffix}"

    def process_file(self, source_path: Path, asset_dir: Path) -> Path:
        """
        Process a single asset file.

        Args:
            source_path: Source file path
            asset_dir: Asset directory containing the file

        Returns:
            Output file path relative to output directory
        """
        # Compute relative path from asset directory
        rel_path = source_path.relative_to(asset_dir)

        # Determine output path
        if self._should_fingerprint(source_path):
            # Compute hash and create fingerprinted name
            content_hash = self._compute_hash(source_path)
            fingerprinted_name = self._fingerprint_filename(source_path, content_hash)

            # Build output path
            output_path = self.config.output_dir / rel_path.parent / fingerprinted_name

            # Store mapping for URL rewriting
            # BUG 5: This doesn't handle nested page paths correctly
            original_url = f"/{rel_path.as_posix()}"
            fingerprinted_url = f"/{rel_path.parent.as_posix()}/{fingerprinted_name}"
            if rel_path.parent == Path("."):
                fingerprinted_url = f"/{fingerprinted_name}"

            self.fingerprint_map[original_url] = fingerprinted_url
        else:
            # Copy without fingerprinting
            output_path = self.config.output_dir / rel_path

        # Copy file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)

        return output_path

    def process_directory(self, asset_dir: Path):
        """
        Process all assets in a directory.

        Args:
            asset_dir: Directory containing assets
        """
        asset_dir = Path(asset_dir)
        if not asset_dir.exists():
            print(f"  Warning: Asset directory not found: {asset_dir}")
            return

        processed_count = 0

        for file_path in asset_dir.rglob("*"):
            if file_path.is_file():
                self.process_file(file_path, asset_dir)
                processed_count += 1

        print(f"  Processed {processed_count} files from {asset_dir.name}")

    def process(self):
        """
        Process all configured asset directories.

        BUG 5: Fingerprinted asset URLs work on root pages but break on nested pages.

        Example:
            Root page (index.html):
                <link rel="stylesheet" href="/style.abc123.css"> ✓ Works

            Nested page (blog/post-1/index.html):
                <link rel="stylesheet" href="/style.abc123.css"> ✓ Works
                BUT if using relative paths:
                <link rel="stylesheet" href="../style.abc123.css"> ✗ Breaks

        The bug is in how fingerprinted URLs are generated - they don't account
        for the depth of the page requesting the asset.
        """
        for asset_dir_name in self.config.asset_dirs:
            # Asset dirs can be relative to content dir or absolute
            asset_dir = Path(asset_dir_name)
            if not asset_dir.is_absolute():
                asset_dir = self.config.content_dir.parent / asset_dir_name

            self.process_directory(asset_dir)

        if self.fingerprint_map:
            print(f"  Generated {len(self.fingerprint_map)} fingerprinted assets")

    def rewrite_asset_urls(self, html: str, page_depth: int = 0) -> str:
        """
        Rewrite asset URLs in HTML to use fingerprinted versions.

        BUG 5 LOCATION: This doesn't adjust URLs based on page depth.

        Args:
            html: HTML content
            page_depth: Depth of the page (0 for root, 1 for /blog/, etc.)

        Returns:
            HTML with rewritten URLs
        """
        # Simple find-and-replace (not production-ready, but adequate)
        for original, fingerprinted in self.fingerprint_map.items():
            html = html.replace(f'href="{original}"', f'href="{fingerprinted}"')
            html = html.replace(f'src="{original}"', f'src="{fingerprinted}"')

        # BUG 5: Doesn't handle relative paths like href="../style.css"
        # These break on nested pages when they should be converted to absolute paths

        return html

    def get_fingerprinted_url(self, original_path: str) -> str:
        """
        Get the fingerprinted URL for an original asset path.

        Args:
            original_path: Original asset path

        Returns:
            Fingerprinted URL if available, otherwise original path
        """
        # Normalize path
        if not original_path.startswith("/"):
            original_path = f"/{original_path}"

        return self.fingerprint_map.get(original_path, original_path)
