"""Module for handling progress indication."""
import sys
import threading
import time
import itertools

class ProgressIndicator:
    """A simple progress indicator that shows animated dots."""
    
    def __init__(self, message="Processing"):
        """Initialize the progress indicator.
        
        Args:
            message: The message to display before the dots
        """
        self.message = message
        self.running = False
        self.thread = None
    
    def _animate(self):
        """Animation loop that displays the progress dots."""
        for dots in itertools.cycle(['   ', '.  ', '.. ', '...']):
            if not self.running:
                break
            sys.stdout.write(f'\r{self.message}{dots}')
            sys.stdout.flush()
            time.sleep(0.25)  # Faster animation
    
    def start(self):
        """Start displaying the progress indicator."""
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.start()
    
    def stop(self):
        """Stop displaying the progress indicator."""
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the line and move to the beginning
        sys.stdout.write('\r' + ' ' * (len(self.message) + 3))
        sys.stdout.write('\r')
        sys.stdout.flush() 