"""Tests for progress indicator functionality."""
import unittest
import time
from unittest.mock import patch, MagicMock
from cpai.progress import ProgressIndicator

class TestProgressIndicator(unittest.TestCase):
    """Test cases for progress indicator."""
    
    def test_init(self):
        """Test progress indicator initialization."""
        progress = ProgressIndicator("Test")
        self.assertEqual(progress.message, "Test")
        self.assertFalse(progress.running)
        self.assertIsNone(progress.thread)

    def test_start_stop(self):
        """Test starting and stopping the progress indicator."""
        progress = ProgressIndicator()
        
        with patch('sys.stdout.write') as mock_write:
            progress.start()
            self.assertTrue(progress.running)
            self.assertIsNotNone(progress.thread)
            
            # Give it time to make at least one update
            time.sleep(0.6)
            
            progress.stop()
            self.assertFalse(progress.running)
            
            # Should have written dots
            mock_write.assert_called()
            # Should have cleared the line at the end
            self.assertEqual(
                mock_write.call_args_list[-1][0][0],
                '\r' + ' ' * (len("Processing") + 3) + '\r'
            )

    def test_custom_message(self):
        """Test progress indicator with custom message."""
        progress = ProgressIndicator("Custom message")
        
        with patch('sys.stdout.write') as mock_write:
            progress.start()
            time.sleep(0.6)
            progress.stop()
            
            # Should have used custom message
            calls = mock_write.call_args_list
            self.assertTrue(any('Custom message' in call[0][0] for call in calls))

    def test_animation_cycle(self):
        """Test that the animation cycles through dots."""
        progress = ProgressIndicator()
        
        with patch('sys.stdout.write') as mock_write:
            progress.start()
            # Wait for two full cycles
            time.sleep(2.1)
            progress.stop()
            
            # Should have shown different dot patterns
            calls = [call[0][0] for call in mock_write.call_args_list]
            patterns = set()
            for call in calls:
                if call.endswith('   '):
                    patterns.add('   ')
                elif call.endswith('.  '):
                    patterns.add('.  ')
                elif call.endswith('.. '):
                    patterns.add('.. ')
                elif call.endswith('...'):
                    patterns.add('...')
            
            # Should have used at least 3 different patterns
            self.assertGreaterEqual(len(patterns), 3)

    def test_multiple_instances(self):
        """Test that multiple progress indicators can run simultaneously."""
        progress1 = ProgressIndicator("First")
        progress2 = ProgressIndicator("Second")
        
        with patch('sys.stdout.write') as mock_write:
            progress1.start()
            progress2.start()
            time.sleep(0.6)
            progress1.stop()
            progress2.stop()
            
            # Should have written both messages
            calls = [call[0][0] for call in mock_write.call_args_list]
            self.assertTrue(any('First' in call for call in calls))
            self.assertTrue(any('Second' in call for call in calls))

if __name__ == '__main__':
    unittest.main() 