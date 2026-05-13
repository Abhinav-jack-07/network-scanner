from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List
import time


@dataclass
class UserState:
    opted_out: bool = False
    human_handoff: bool = False
    history: List[Dict[str, str]] = field(default_factory=list)
    message_timestamps: Deque[float] = field(default_factory=deque)


class StateStore:
    def __init__(self, max_history: int, rate_limit_window_seconds: int, rate_limit_max: int) -> None:
        self._states: Dict[str, UserState] = {}
        self._max_history = max_history
        self._rate_limit_window_seconds = rate_limit_window_seconds
        self._rate_limit_max = rate_limit_max

    def get(self, user_id: str) -> UserState:
        if user_id not in self._states:
            self._states[user_id] = UserState()
        return self._states[user_id]

    def add_history(self, user_state: UserState, role: str, content: str) -> None:
        user_state.history.append({"role": role, "content": content})
        if len(user_state.history) > self._max_history:
            user_state.history = user_state.history[-self._max_history :]

    def record_message(self, user_state: UserState) -> None:
        now = time.time()
        user_state.message_timestamps.append(now)
        self._trim_timestamps(user_state, now)

    def is_rate_limited(self, user_state: UserState) -> bool:
        now = time.time()
        self._trim_timestamps(user_state, now)
        return len(user_state.message_timestamps) >= self._rate_limit_max

    def _trim_timestamps(self, user_state: UserState, now: float) -> None:
        cutoff = now - self._rate_limit_window_seconds
        while user_state.message_timestamps and user_state.message_timestamps[0] < cutoff:
            user_state.message_timestamps.popleft()
