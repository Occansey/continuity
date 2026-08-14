"""The one measurement in the project that is not a judgement: can the prior art register
this pair at all?

reachability.py runs the competitor's own technique — ORB features, RANSAC homography — and
reports a count of geometric inliers. These tests drive it with tiny synthetic frames written
to a temp dir and assert on the Reachability object it returns, never on the reason string as
a label. Two views of the same scene must register (the prior art reaches them); a structured
frame against pure noise must not (only a content method reaches that); a missing frame fails
safe with a reason.
"""
import cv2
import numpy as np
import pytest
from continuity.reachability import MIN_INLIERS, registrable


def _structured(seed: int) -> np.ndarray:
    """A frame full of corners — the features ORB is built to find. Deterministic per seed
    so the test is reproducible; registration cares about geometry, not the RNG."""
    rng = np.random.default_rng(seed)
    img = np.full((400, 400), 128, np.uint8)
    for _ in range(12):
        x, y = int(rng.integers(20, 340)), int(rng.integers(20, 340))
        w, h = int(rng.integers(20, 60)), int(rng.integers(20, 60))
        cv2.rectangle(img, (x, y), (x + w, y + h), int(rng.integers(0, 255)), -1)
        cx, cy = int(rng.integers(30, 370)), int(rng.integers(30, 370))
        cv2.circle(img, (cx, cy), int(rng.integers(10, 30)), int(rng.integers(0, 255)), -1)
    return img


@pytest.fixture
def frames(tmp_path):
    """Write a base frame, a small-shift copy of it, and a pure-noise frame to disk, and
    hand back the paths. registrable reads from paths, so the frames must be real files."""
    base = _structured(0)
    cv2.imwrite(str(tmp_path / "a.png"), base)

    shifted = cv2.warpAffine(base, np.float32([[1, 0, 4], [0, 1, 3]]), (400, 400))
    cv2.imwrite(str(tmp_path / "a_shift.png"), shifted)

    noise = np.random.default_rng(99).integers(0, 255, (400, 400), dtype=np.uint8)
    cv2.imwrite(str(tmp_path / "noise.png"), noise)
    return tmp_path


def test_identical_frames_register(frames):
    """Two identical frames are the easy case the prior art was built for. If this pair does
    not register, the measurement is broken and every unreachable claim is suspect."""
    r = registrable(frames / "a.png", frames / "a.png")
    assert r.reachable is True
    assert r.inliers >= MIN_INLIERS


def test_a_small_shift_still_registers(frames):
    """A few pixels of camera drift is exactly what registration is meant to warp away, so a
    near-identical view must still come back reachable with a healthy inlier count."""
    r = registrable(frames / "a.png", frames / "a_shift.png")
    assert r.reachable is True
    assert r.inliers >= MIN_INLIERS


def test_structure_against_noise_does_not_register(frames):
    """A structured frame and pure random noise share no real geometry. RANSAC must not fit a
    homography that means anything, so the pair is unreachable — the class only a content
    method can connect."""
    r = registrable(frames / "a.png", frames / "noise.png")
    assert r.reachable is False
    assert r.inliers < MIN_INLIERS


def test_a_missing_frame_fails_safe_with_a_reason(frames):
    """A frame that will not read is not a pair the prior art secretly reaches — it is no
    measurement at all. It must come back unreachable and say why, not raise or pass."""
    r = registrable(frames / "does_not_exist.png", frames / "a.png")
    assert r.reachable is False
    assert r.inliers == 0
    assert "missing" in r.reason
