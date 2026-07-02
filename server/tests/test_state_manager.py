"""
server/tests/test_state_manager.py
===================================
Unit tests for Room and User state tracking metrics.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from state_manager import get_room_session_state

class TestStateManager(unittest.TestCase):

    def test_room_state_tracking(self):
        room_state = get_room_session_state("test_unit_room_1")
        
        # Register messages
        for _ in range(8):
            room_state.register_message("Student_A", "normal")
        for _ in range(2):
            room_state.register_message("Student_B", "normal")
            
        dominant = room_state.get_dominant_user()
        self.assertEqual(dominant, "Student_A")
        
        # Test completion state
        room_state.register_message("Student_B", "ranking_complete")
        u_b = room_state.get_user("Student_B")
        self.assertTrue(u_b.completed_ranking)

if __name__ == "__main__":
    unittest.main()
