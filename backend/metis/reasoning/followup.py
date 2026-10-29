"""Bounded local evidence snapshots, not conversation/session storage.

Clients may reference backend-owned evidence, never supply replacement truth.
Restart/eviction expires the reference explicitly; no current-context fallback.
"""
from collections import OrderedDict
from copy import deepcopy
from secrets import token_urlsafe
from threading import Lock
from typing import Literal
import os

from pydantic import BaseModel, ConfigDict, Field

from metis.reasoning.harness import DemoProvider, HTTPProvider, ReasoningRequest, Turn
from metis.verification.claims import verify_claims


class InvestigationRequest(ReasoningRequest):
    investigation_scope: Literal['daily', 'scenario'] = 'scenario'


class FollowupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=2000, pattern=r'\S')
    investigation_id: str = Field(min_length=20, max_length=100)
    history: list[Turn] = Field(default_factory=list, max_length=6)


class SnapshotUnavailable(Exception):
    pass


class EvidenceSnapshots:
    def __init__(self, capacity=128):
        self.capacity = capacity
        self._items = OrderedDict()
        self._lock = Lock()

    def capture(self, result, scope):
        result = deepcopy(result)
        result['investigation_id'] = token_urlsafe(24)
        result['investigation_scope'] = scope
        result['context']['investigation_scope'] = scope
        # Keep evidence/provider metadata only; conversation stays in the browser.
        saved = {key: result[key] for key in ['investigation_id', 'investigation_scope', 'context',
                 'context_operations', 'context_mode', 'mode', 'model']}
        with self._lock:
            self._items[result['investigation_id']] = deepcopy(saved)
            while len(self._items) > self.capacity:
                self._items.popitem(last=False)
        return result

    def resume(self, request: FollowupRequest):
        with self._lock:
            saved = deepcopy(self._items.get(request.investigation_id))
        if saved is None:
            raise SnapshotUnavailable('Captured investigation is no longer available. Start a new daily or scenario investigation; no current calculation was substituted.')
        if saved['context_mode'] == 'evidence_only' and request.history:
            raise SnapshotUnavailable('Evidence-only investigations do not accept conversation history. Start a new investigation with empty history.')
        # Preserve demo/live identity too; a configuration change requires an explicit new investigation.
        if os.getenv('METIS_PROVIDER', 'demo').strip().lower() != saved['mode']:
            raise SnapshotUnavailable('Provider mode changed. Start a new investigation; the captured answer was preserved.')
        provider = DemoProvider() if saved['mode'] == 'demo' else HTTPProvider(saved['mode'])
        if saved['mode'] != 'demo' and provider.model != saved['model']:
            raise SnapshotUnavailable('Provider model changed. Start a new investigation; the captured answer was preserved.')
        interpretation_request = ReasoningRequest(question=request.question, history=request.history,
            shocks=saved['context']['scenario']['shocks'], context_mode=saved['context_mode'])
        # Provider receives an isolated copy; verification always uses the captured backend evidence.
        result = provider.interpret(interpretation_request, deepcopy(saved['context']))
        return saved | {'question': request.question, 'interpretation': result.model_dump(),
                        'verification': verify_claims(result.financial_claims, saved['context']),
                        'usage': None if saved['mode'] == 'demo' else provider.last_usage}
