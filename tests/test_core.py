"""Unit tests for Swarm Byzantine State Arbiter."""
import unittest
from swarm_byzantine_state_arbiter.core import ByzantineStateArbiter, ConsensusVote

class TestByzantineStateArbiter(unittest.TestCase):
    def setUp(self):
        self.nodes = [f"agent_{i}" for i in range(1, 8)]
        self.arbiter = ByzantineStateArbiter("agent_1", self.nodes)

    def test_quorum_calculation(self):
        # N=7, f=2, 2f+1 = 5
        self.assertEqual(self.arbiter.f, 2)
        self.assertEqual(self.arbiter.get_quorum_threshold(), 5)

    def test_successful_commit_flow(self):
        prop = self.arbiter.create_proposal("p1", {"key": "val1"})
        quorum = None
        for node in self.nodes[:5]:
            vote = ConsensusVote(node, prop.proposal_id, prop.epoch, prop.digest, True)
            quorum = self.arbiter.receive_vote(vote)
        
        self.assertIsNotNone(quorum)
        self.assertTrue(quorum.committed)
        state = self.arbiter.commit_proposal(prop, quorum)
        self.assertEqual(state["key"], "val1")
        self.assertEqual(len(self.arbiter.commit_log), 1)

    def test_unauthorized_node_rejected(self):
        prop = self.arbiter.create_proposal("p2", {"foo": "bar"})
        with self.assertRaises(ValueError):
            self.arbiter.receive_vote(ConsensusVote("rogue_agent", prop.proposal_id, prop.epoch, prop.digest, True))
