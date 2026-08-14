"""Confirm an error verdict by making it survive an adversary.

Adjudication says 'error'. That is one model's opinion, and a tool whose metric is precision
cannot ship an opinion as a finding. So every error faces a second model whose only job is to
explain it away (verify.skeptic). A flag that survives a skeptic built to kill it is evidence;
one that does not is downgraded. The survival rate is the precision signal — reported, not
asserted, and it needs no human judge, which is the whole point.

This is the same adversarial-verify pattern the sibling project used: default toward keeping
the flag when the skeptic's output cannot be read, so a broken adversary never silently
discards a real finding.
"""

from __future__ import annotations

from continuity.frame_of_reference import REFERENCE
from continuity.verify import skeptic


def confirm(client, verdict, model: str) -> dict:
    """Return {survived: bool, reason: str} for one adjudicated finding.

    Only 'error' verdicts are worth attacking; anything else passes through as survived
    (there is nothing to refute about 'explained')."""
    if getattr(verdict, "verdict", None) != "error":
        return {"survived": True, "reason": "not an error verdict; nothing to refute"}
    finding = (f"{verdict.entity} — {verdict.attribute}: "
               f"'{verdict.value_from}' at {verdict.t_from:.0f}s becomes "
               f"'{verdict.value_to}' at {verdict.t_to:.0f}s. Reason given: {verdict.reason}")
    # A world-relative fact — a watch on a wrist, a scar on a cheek — cannot be explained
    # away by time passing or a camera angle, because it is fixed to the body, not the frame.
    # Without this the skeptic refuted every finding with a generic "time elapsed", which
    # made it a nihilist rather than a filter: it would kill real errors too. This is where
    # the frame-of-reference model earns its place — it tells the skeptic which excuses are
    # off-limits.
    if REFERENCE.get(verdict.attribute) == "world":
        finding += (" NOTE: this attribute is fixed to the body, not the camera. Elapsed "
                    "time, a scene change, or a different camera angle do NOT explain it — "
                    "a person does not move a watch to the other wrist, or a scar to the "
                    "other cheek, off screen. Only refute with a specific, grounded reason.")
    s = skeptic(client, finding, model)
    return {"survived": not s["refuted"], "reason": s["reason"]}
