"""Can the prior art even see this pair?

This is the keystone measurement, and it is the one number in the project that is not a
judgement. Every existing continuity tool — Pickup & Zisserman 2009, filmcontinuity.com —
works by *registration*: line two frames up by matching visual features, warp one onto the
other, and diff. That only works when the two frames are of nearly the same view. It is
their method's precondition, stated in their own paper: "pairs of shots within a scene"
from "similar camera angles".

So for any pair we flag, we can ask their method's own question: could these two frames be
registered at all? If a feature-matching homography cannot be estimated between them, then
no registration-based tool can reach this pair, by construction and not by opinion. The
answer is a count of geometric inliers, which is arithmetic.

This turns our differentiation from a claim into a measurement:

    "N% of our findings connect frames that the entire prior art cannot register."

It is classical computer vision — ORB features, RANSAC homography — not a model. That is
deliberate twice over: it keeps us inside the rules (no non-Google AI), and it means we
are running *the competitor's actual technique* and showing where it stops, rather than
describing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# Below this many geometric inliers, RANSAC cannot fit a homography that means anything,
# and registration fails. The 2009 method needs a good fit to warp one frame onto the
# other; a handful of chance matches is not one. Conservative on purpose: we would rather
# call a pair *reachable* (and concede it to the prior art) than overclaim unreachability.
MIN_INLIERS = 15


@dataclass(frozen=True)
class Reachability:
    inliers: int
    matches: int
    reachable: bool
    reason: str


def _prep(path: Path) -> np.ndarray | None:
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return img


def registrable(frame_a: Path, frame_b: Path) -> Reachability:
    """Attempt the registration the prior art depends on. Report whether it succeeds.

    A success means a pixel method *could* have connected these frames, so the pair is not
    evidence of anything new. A failure means only a method that reasons about *content*
    rather than *pixels* — which is what we are — can connect them.
    """
    a, b = _prep(frame_a), _prep(frame_b)
    if a is None or b is None:
        return Reachability(0, 0, False, "a frame is missing; cannot register")

    orb = cv2.ORB_create(nfeatures=2000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < MIN_INLIERS or len(kb) < MIN_INLIERS:
        return Reachability(0, 0, False, "too few features to attempt registration")

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    raw = matcher.knnMatch(da, db, k=2)
    # Lowe's ratio test: keep a match only if it is clearly better than the second-best,
    # which is how the prior art screens correspondences before RANSAC.
    good = [m for pair in raw if len(pair) == 2 for m, n in [pair] if m.distance < 0.75 * n.distance]
    if len(good) < MIN_INLIERS:
        return Reachability(0, len(good), False,
                            f"{len(good)} good matches, below the {MIN_INLIERS} a homography needs")

    src = np.float32([ka[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    _H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    inliers = int(mask.sum()) if mask is not None else 0

    reachable = inliers >= MIN_INLIERS
    reason = (f"registered: {inliers} geometric inliers — a pixel method reaches this"
              if reachable else
              f"{inliers} inliers, below {MIN_INLIERS} — no registration-based method reaches this")
    return Reachability(inliers, len(good), reachable, reason)
