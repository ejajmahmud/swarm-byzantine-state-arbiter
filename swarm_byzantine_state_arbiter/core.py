"""Core Byzantine Fault Tolerant State Arbiter."""
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Set

class Proposal:
    def __init__(self, proposal_id: str, epoch: int, proposer_id: str, state_delta: Dict[str, Any]):
        self.proposal_id = proposal_id
        self.epoch = epoch
        self.proposer_id = proposer_id
        self.state_delta = state_delta
        self.timestamp = time.time()
        self.digest = self._calculate_digest()

    def _calculate_digest(self) -> str:
        serialized = json.dumps({
            "id": self.proposal_id,
            "epoch": self.epoch,
            "proposer": self.proposer_id,
            "delta": self.state_delta
        }, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

class ConsensusVote:
    def __init__(self, voter_id: str, proposal_id: str, epoch: int, digest: str, approved: bool):
        self.voter_id = voter_id
        self.proposal_id = proposal_id
        self.epoch = epoch
        self.digest = digest
        self.approved = approved

class QuorumResult:
    def __init__(self, committed: bool, epoch: int, proposal_id: str, digest: str, vote_count: int, total_nodes: int):
        self.committed = committed
        self.epoch = epoch
        self.proposal_id = proposal_id
        self.digest = digest
        self.vote_count = vote_count
        self.total_nodes = total_nodes

class ByzantineStateArbiter:
    def __init__(self, node_id: str, swarm_nodes: List[str]):
        self.node_id = node_id
        self.swarm_nodes = set(swarm_nodes)
        self.total_nodes = len(self.swarm_nodes)
        self.f = (self.total_nodes - 1) // 3
        self.current_epoch = 0
        self.state: Dict[str, Any] = {}
        self.commit_log: List[Dict[str, Any]] = []
        self._prepare_votes: Dict[str, Dict[str, bool]] = {}

    def get_quorum_threshold(self) -> int:
        return 2 * self.f + 1

    def create_proposal(self, proposal_id: str, state_delta: Dict[str, Any]) -> Proposal:
        self.current_epoch += 1
        return Proposal(proposal_id, self.current_epoch, self.node_id, state_delta)

    def receive_vote(self, vote: ConsensusVote) -> Optional[QuorumResult]:
        if vote.voter_id not in self.swarm_nodes:
            raise ValueError(f"Unauthorized voter node: {vote.voter_id}")
        
        prop_id = vote.proposal_id
        if prop_id not in self._prepare_votes:
            self._prepare_votes[prop_id] = {}
        
        self._prepare_votes[prop_id][vote.voter_id] = vote.approved
        
        approvals = sum(1 for v in self._prepare_votes[prop_id].values() if v)
        threshold = self.get_quorum_threshold()
        
        if approvals >= threshold:
            return QuorumResult(
                committed=True,
                epoch=vote.epoch,
                proposal_id=prop_id,
                digest=vote.digest,
                vote_count=approvals,
                total_nodes=self.total_nodes
            )
        return None

    def commit_proposal(self, proposal: Proposal, quorum: QuorumResult) -> Dict[str, Any]:
        if not quorum.committed or quorum.proposal_id != proposal.proposal_id:
            raise RuntimeError("Cannot commit proposal without valid quorum confirmation")
        if quorum.digest != proposal.digest:
            raise ValueError("Quorum digest mismatch with proposal digest")
        
        # Apply state transition
        self.state.update(proposal.state_delta)
        entry = {
            "epoch": proposal.epoch,
            "proposal_id": proposal.proposal_id,
            "digest": proposal.digest,
            "votes": quorum.vote_count,
            "delta": proposal.state_delta
        }
        self.commit_log.append(entry)
        return self.state
