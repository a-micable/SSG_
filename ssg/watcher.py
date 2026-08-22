"""
File watching for development mode.
Automatically rebuilds site when content or templates change.
"""

import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class WatcherError(Exception):
    """Raised when file watching fails."""

    pass


class ChangeHandler(FileSystemEventHandler):
    """
    Handles file system change events.
    """

    def __init__(self, callback: Callable[[list[Path]], None], debounce_seconds: float = 0.5):
        """
        Initialize the change handler.

        Args:
            callback: Function to call when changes are detected
            debounce_seconds: Seconds to wait before triggering callback
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.changed_files: set[Path] = set()
        self.last_trigger = 0.0

    def on_any_event(self, event: FileSystemEvent):
        """
        Handle any file system event.

        Args:
            event: File system event
        """
        # Ignore directory events
        if event.is_directory:
            return

        # Ignore certain file patterns
        path = Path(event.src_path)
        if self._should_ignore(path):
            return

        # Track changed file
        self.changed_files.add(path)

        # Trigger callback after debounce period
        current_time = time.time()
        if current_time - self.last_trigger >= self.debounce_seconds:
            self._trigger_callback()

    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a file should be ignored.

        Args:
            path: File path

        Returns:
            True if file should be ignored
        """
        # Ignore hidden files
        if path.name.startswith("."):
            return True

        # Ignore common temporary files
        ignore_suffixes = [".swp", ".tmp", "~", ".pyc", ".pyo"]
        if path.suffix in ignore_suffixes:
            return True

        # Ignore __pycache__ directories
        if "__pycache__" in path.parts:
            return True

        return False

    def _trigger_callback(self):
        """Trigger the callback with accumulated changes."""
        if self.changed_files:
            changed = list(self.changed_files)
            self.changed_files.clear()
            self.last_trigger = time.time()

            try:
                self.callback(changed)
            except Exception as e:
                print(f"Error in change callback: {e}")


class FileWatcher:
    """
    Watches directories for file changes and triggers rebuilds.
    """

    def __init__(self, callback: Callable[[list[Path]], None]):
        """
        Initialize the file watcher.

        Args:
            callback: Function to call when changes are detected
        """
        self.callback = callback
        self.observer = Observer()
        self.watched_paths: set[Path] = set()

    def watch(self, path: Path, recursive: bool = True):
        """
        Start watching a directory for changes.

        Args:
            path: Directory to watch
            recursive: Whether to watch subdirectories
        """
        if not path.exists():
            raise WatcherError(f"Path does not exist: {path}")

        if not path.is_dir():
            raise WatcherError(f"Path is not a directory: {path}")

        # Create handler
        handler = ChangeHandler(self.callback)

        # Schedule observer
        self.observer.schedule(handler, str(path), recursive=recursive)
        self.watched_paths.add(path)

        print(f"Watching: {path}")

    def start(self):
        """Start the file watcher."""
        if not self.watched_paths:
            raise WatcherError("No paths are being watched")

        print("Starting file watcher...")
        self.observer.start()

    def stop(self):
        """Stop the file watcher."""
        print("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()

    def run(self):
        """
        Start watching and block until interrupted.

        This is the main entry point for watch mode.
        """
        self.start()

        try:
            print("\nWatching for changes... (Press Ctrl+C to stop)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            self.stop()
