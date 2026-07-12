from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API_BASE = "https://codeforces.com/api"


class CodeforcesApiError(RuntimeError):
    pass


@dataclass
class CodeforcesClient:
    delay_seconds: float = 2.1
    timeout_seconds: int = 30
    user_agent: str = "cfdb-ingestor/0.1"

    def __post_init__(self) -> None:
        self._last_request_at = 0.0

    def _wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

    def call(self, method: str, **params: Any) -> Any:
        self._wait()
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{API_BASE}/{method}"
        if query:
            url = f"{url}?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        self._last_request_at = time.monotonic()
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("status") != "OK":
            raise CodeforcesApiError(payload.get("comment", "Codeforces API returned non-OK status"))
        return payload["result"]

    def contest_list(self, gym: bool = False) -> list[dict[str, Any]]:
        return self.call("contest.list", gym=str(gym).lower())

    def contest_standings(self, contest_id: int) -> dict[str, Any]:
        return self.call("contest.standings", contestId=contest_id)

    def problemset_problems(self) -> dict[str, Any]:
        return self.call("problemset.problems")

    def user_status(
        self,
        handle: str,
        *,
        offset: int = 1,
        count: int = 1000,
    ) -> list[dict[str, Any]]:
        return self.call("user.status", handle=handle, **{"from": offset}, count=count)
