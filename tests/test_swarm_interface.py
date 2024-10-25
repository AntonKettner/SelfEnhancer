import unittest
from src.swarm_interface import SwarmInterface


class TestSwarmInterface(unittest.TestCase):
    def test_swarm_interface_initialization(self):
        interface = SwarmInterface()
        self.assertIsInstance(interface, SwarmInterface)


if __name__ == "__main__":
    unittest.main()
