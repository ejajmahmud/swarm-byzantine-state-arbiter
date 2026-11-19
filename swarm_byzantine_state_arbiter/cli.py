"""CLI interface for Swarm Byzantine State Arbiter."""
import argparse
import sys
from .core import ByzantineStateArbiter, ConsensusVote

def main():
    parser = argparse.ArgumentParser(description="Swarm Byzantine State Arbiter CLI")
    parser.add_argument("--demo", action="store_true", help="Run BFT quorum demonstration")
    args = parser.parse_args()

    nodes = [f"agent-{i}" for i in range(1, 8)]
    arbiter = ByzantineStateArbiter(node_id="agent-1", swarm_nodes=nodes)
    prop = arbiter.create_proposal("prop-001", {"policy": "enforce_rate_limits", "max_tokens": 4096})
    print(f"Created proposal {prop.proposal_id} with digest {prop.digest[:16]}...")
    
    quorum = None
    for n in nodes[:5]:
        v = ConsensusVote(voter_id=n, proposal_id=prop.proposal_id, epoch=prop.epoch, digest=prop.digest, approved=True)
        quorum = arbiter.receive_vote(v)
    
    if quorum and quorum.committed:
        arbiter.commit_proposal(prop, quorum)
        print(f"Quorum reached! Committed proposal at epoch {quorum.epoch}. Current state: {arbiter.state}")
    else:
        print("Failed to reach quorum.")

if __name__ == "__main__":
    main()
