import unittest
from src.agent import Agent


class TestAgent(unittest.TestCase):
    def test_agent_initialization(self):
        agent = Agent()
        self.assertIsInstance(agent, Agent)


if __name__ == "__main__":
    unittest.main()
