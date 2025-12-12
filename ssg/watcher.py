"""
File watching for development mode.

Monitors content, template, and asset changes and triggers rebuilds.
"""

import logging
import time
from pathlib import Path
from typing import Callable, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ssg.config import SiteConfig

logger = logging.getLogger(__name__)


class SiteWatcher(FileSystemEventHandler):
    """
    Watches for file changes and triggers rebuilds.
    
    Monitors:
    - Content directory for Markdown changes
    - Template directory for template changes
    - Asset directory for static file changes
    """

    def __init__(
        self,
        config: SiteConfig,
        on_change: Callable[[Set[Path]], None],
        debounce_seconds: float = 0.5,
    ) -> None:
        """
        Initialize file watcher.
        
        Args:
            config: Site configuration
            on_change: Callback function to invoke with changed files
            debounce_seconds: Time to wait for additional changes before triggering
        """
        super().__init__()
        self.config = config
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds
        
        self.changed_files: Set[Path] = set()
        self.last_change_time: float = 0

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_change(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_change(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            self._handle_change(event.src_path)

    def _handle_change(self, file_path: str) -> None:
        """
        Handle a file change event.
        
        Args:
            file_path: Path to changed file
        """
        path = Path(file_path)
        
        # Filter relevant files
        if self._should_watch(path):
            self.changed_files.add(path)
            self.last_change_time = time.time()
            logger.debug(f"Detected change: {path}")

    def _should_watch(self, path: Path) -> bool:
        """
        Check if a file should trigger rebuilds.
        
        Args:
            path: File path to check
            
        Returns:
            True if file should be watched
        """
        # Watch Markdown files in content directory
        if path.suffix == ".md" and self._is_under(path, self.config.content_dir):
            return True
        
        # Watch HTML templates
        if path.suffix == ".html" and self._is_under(path, self.config.template_dir):
            return True
        
        # Watch common asset types
        asset_dir = self.config.content_dir.parent / "assets"
        if self._is_under(path, asset_dir):
            asset_extensions = {".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".svg"}
            if path.suffix.lower() in asset_extensions:
                return True
        
        # Ignore output directory
        if self._is_under(path, self.config.output_dir):
            return False
        
        # Ignore hidden files and system files
        if any(part.startswith(".") for part in path.parts):
            return False
        
        return False

    def _is_under(self, path: Path, directory: Path) -> bool:
        """
        Check if path is under directory.
        
        Args:
            path: File path
            directory: Directory path
            
        Returns:
            True if path is under directory
        """
        try:
            path.resolve().relative_to(directory.resolve())
            return True
        except ValueError:
            return False

    def check_and_trigger(self) -> None:
        """
        Check if enough time has passed since last change and trigger rebuild.
        
        This implements debouncing to avoid rebuilding on every keystroke.
        """
        if not self.changed_files:
            return

        # Check if debounce period has elapsed
        elapsed = time.time() - self.last_change_time
        if elapsed >= self.debounce_seconds:
            # Trigger rebuild
            files_to_rebuild = self.changed_files.copy()
            self.changed_files.clear()
            
            logger.info(f"Triggering rebuild for {len(files_to_rebuild)} changed files")
            
            try:
                self.on_change(files_to_rebuild)
            except Exception as e:
                logger.error(f"Rebuild failed: {e}")


def watch_site(config: SiteConfig, on_change: Callable[[Set[Path]], None]) -> None:
    """
    Start watching the site for changes.
    
    Args:
        config: Site configuration
        on_change: Callback for file changes
    """
    logger.info("Starting file watcher")
    
    watcher = SiteWatcher(config, on_change)
    observer = Observer()
    
    # Watch content directory
    if config.content_dir.exists():
        observer.schedule(watcher, str(config.content_dir), recursive=True)
        logger.info(f"Watching content: {config.content_dir}")
    
    # Watch template directory
    if config.template_dir.exists():
        observer.schedule(watcher, str(config.template_dir), recursive=True)
        logger.info(f"Watching templates: {config.template_dir}")
    
    # Watch asset directory
    asset_dir = config.content_dir.parent / "assets"
    if asset_dir.exists():
        observer.schedule(watcher, str(asset_dir), recursive=True)
        logger.info(f"Watching assets: {asset_dir}")
    
    observer.start()
    
    try:
        while True:
            time.sleep(0.1)
            watcher.check_and_trigger()
    except KeyboardInterrupt:
        logger.info("Stopping file watcher")
        observer.stop()
    
    observer.join()
