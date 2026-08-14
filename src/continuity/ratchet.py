"""Earned autonomy, per error class — the mechanism spec §9.5 asks to demonstrate: one
class carried from silent to interrupting, with the ledger visible.

An agent that could interrupt the floor from its first shot would be switched off on its
first false alarm, and rightly. So authority is not configured, it is *earned*, one error
class at a time (`accessory-swap`, `injury-moved`, ...), and only ever in exchange for
calls a human confirmed clean:

- **SHADOW** — records what it would have said and interrupts nothing. Every class starts
  here, because the cost of a false alarm on a working set is a crew's time and two of
  them get the tool switched off (adjudicate.py says the same about `error`).
- **PROVISIONAL** — after a streak of `n` clean confirmed calls, the class may surface in
  dailies review, where a wrong flag costs a moment and not a take.
- **LIVE** — after `m` more, it may interrupt the floor.

The asymmetry is the whole point, and it is the house rule from CLAUDE.md §3: nothing
widens on its own. A streak of confirmed-clean calls is the *only* door that raises
authority. Every other door clamps — one rejected flag demotes the class a rung and resets
its streak, and `restrict` can lower a class but can never lift it. Attack and failure
history may raise scrutiny and may never lower it; a control that could be talked back up
after it misfired is a control that can be trained to misfire.

The ledger is append-only (CLAUDE.md §3) because the agent is the thing being audited: it
exposes no delete, amend, clear or purge, and authority is *derived* by replaying the
recorded history rather than stored as a mutable number someone could nudge. There is no
in-place authority to nudge.
"""

from __future__ import annotations

from enum import IntEnum


class Authority(IntEnum):
    # Ordered, so `<` and `min` mean what they say: a demotion is `Authority(auth - 1)`
    # and a clamp is `min(auth, ceiling)`. SHADOW is the floor a class can never fall
    # below and the default for a class nobody has confirmed anything about.
    SHADOW = 0
    PROVISIONAL = 1
    LIVE = 2


class Ledger:
    """Append-only record of confirmed calls and clamps, per error class.

    Authority is not a field; it is replayed from the log on every read. That is what
    makes "append-only" true rather than aspirational — there is no stored authority for a
    delete or an amend to reach, so the absence of those methods is the guarantee, not a
    promise about how they would behave.
    """

    def __init__(self, n: int = 5, m: int = 5):
        # n: clean calls to earn PROVISIONAL from SHADOW. m: clean calls to earn LIVE from
        # PROVISIONAL. Defaults small enough to demonstrate on one class in a screening,
        # cautious enough that a single class does not reach the floor on a fluke.
        self._n = n
        self._m = m
        self._events: list[tuple] = []

    def record(self, cls: str, accepted: bool) -> Authority:
        """Log the outcome of one confirmed call for `cls` and return its resulting
        authority. `accepted` is a human's verdict on the flag, not the agent's own
        confidence: an accepted call lengthens the streak toward promotion; a rejected one
        (a false alarm a human threw out) demotes the class a rung at once."""
        self._events.append(("call", cls, bool(accepted)))
        return self.authority_of(cls)

    def restrict(self, cls: str, to: Authority) -> Authority:
        """Clamp `cls` down to at most `to` and return its resulting authority. A restrict
        that names a level at or above the class's current authority does nothing: this
        door only ever closes. Re-earning past a clamp is possible, but solely through the
        clean-call streak — never by calling restrict with a higher level."""
        self._events.append(("restrict", cls, Authority(to)))
        return self.authority_of(cls)

    def authority_of(self, cls: str) -> Authority:
        auth = Authority.SHADOW
        streak = 0
        for kind, ev_cls, payload in self._events:
            if ev_cls != cls:
                continue
            if kind == "call":
                if payload:  # accepted: a clean call earns toward the next rung
                    streak += 1
                    need = self._n if auth == Authority.SHADOW else self._m
                    if auth < Authority.LIVE and streak >= need:
                        auth = Authority(auth + 1)
                        streak = 0
                else:  # rejected: a false alarm demotes one rung and the streak is spent
                    auth = Authority(max(Authority.SHADOW, auth - 1))
                    streak = 0
            else:  # restrict: clamp down only, and force the streak to be re-earned
                if payload < auth:
                    auth = payload
                    streak = 0
        return auth
