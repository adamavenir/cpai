"""Progress indicator functionality."""

import sys
import threading
import time
from typing import Optional

class ProgressIndicator:
    """Progress indicator that shows a growing number of dots."""
    
    def __init__(self, prefix: str = "Processing", config: dict = None):
        """Initialize progress indicator.
        
        Args:
            prefix: Text to show before the dots
            config: Configuration dictionary
        """
        self.prefix = prefix
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.start_time = 0
        self.config = config or {}
        
    def _show_progress(self):
        """Show progress with growing dots."""
        # Don't show progress in stdout mode
        if self.config.get('stdout'):
            return
            
        dots = 3
        sys.stderr.write(f"{self.prefix}{'.' * dots}")  # Start with three dots
        sys.stderr.flush()
        
        while self.is_running:
            time.sleep(0.5)  # Wait half a second
            if self.is_running:  # Check again after sleep
                dots += 1
                sys.stderr.write(f"\r{self.prefix}{'.' * dots}")
                sys.stderr.flush()
    
    def start(self):
        """Start showing progress."""
        self.is_running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._show_progress)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop showing progress."""
        self.is_running = False
        if self.thread:
            self.thread.join()
        # Add newline to separate from next output
        if not self.config.get('stdout'):
            sys.stderr.write('\n') 