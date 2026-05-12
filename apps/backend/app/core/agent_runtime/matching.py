from __future__ import annotations

from dataclasses import dataclass

from app.core.agent_runtime.registry import AgentRegistry
from app.models.agent import Agent


@dataclass(frozen=True)
class AgentMatch:
    agent: Agent | None
    score: float
    matched_capabilities: list[str]
    missing_capabilities: list[str]
    fallback_used: bool
    reason: str


class CapabilityMatcher:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def find_best_agent(
        self,
        department: str,
        required_capabilities: list[str],
    ) -> AgentMatch:
        candidates = self.registry.list_available_agents()

        if not candidates:
            return AgentMatch(
                agent=None,
                score=0,
                matched_capabilities=[],
                missing_capabilities=required_capabilities,
                fallback_used=False,
                reason="no_available_agents",
            )

        scored = [
            self._score_agent(
                agent,
                department,
                required_capabilities,
            )
            for agent in candidates
        ]
        scored.sort(
            key=lambda item: (
                item.score,
                -item.agent.workload,
                item.agent.performance_score,
                item.agent.name,
            ),
            reverse=True,
        )

        best = scored[0]

        if best.score <= 0:
            return AgentMatch(
                agent=None,
                score=0,
                matched_capabilities=[],
                missing_capabilities=required_capabilities,
                fallback_used=False,
                reason="no_capable_agent",
            )

        perfect = (
            best.agent.department == department
            and not best.missing_capabilities
        )

        return AgentMatch(
            agent=best.agent,
            score=best.score,
            matched_capabilities=best.matched_capabilities,
            missing_capabilities=best.missing_capabilities,
            fallback_used=not perfect,
            reason="matched" if perfect else "fallback",
        )

    def _score_agent(
        self,
        agent: Agent,
        department: str,
        required_capabilities: list[str],
    ) -> AgentMatch:
        agent_capabilities = set(agent.capabilities)
        required = set(required_capabilities)
        matched = sorted(required & agent_capabilities)
        missing = sorted(required - agent_capabilities)

        score = 0.0

        if agent.department == department:
            score += 40

        if required:
            score += 15 * len(matched)
            score -= 8 * len(missing)
        else:
            score += 10

        score += agent.performance_score * 10
        score -= agent.workload * 5

        return AgentMatch(
            agent=agent,
            score=score,
            matched_capabilities=matched,
            missing_capabilities=missing,
            fallback_used=False,
            reason="scored",
        )
