"""The left/right frame-of-reference filter: the mirror artifact V1 kept reporting.

No model here — this is arithmetic on tokens, and the point is that it stays that way."""
from continuity.frame_of_reference import REFERENCE, is_spurious_flip, GUIDANCE

# The store's schema attribute vocabulary. If the schema grows, REFERENCE must too, so the
# table is checked against the full list rather than a sample.
SCHEMA_ATTRIBUTES = [
    "wearing", "holding", "hair", "injury", "facial_hair", "accessory",
    "position", "time_of_day", "weather", "location", "vehicle_state", "prop_state",
]


def test_a_person_screen_side_flip_is_spurious():
    """Reverse angle: the same person, left of one frame, right of the next. The camera
    moved, not the person."""
    assert is_spurious_flip("position", "screen left", "screen right") is True


def test_an_accessory_wrist_swap_is_not_spurious():
    """A watch is on the wrist it is on from every angle. If it swaps, that is the finding,
    and the mirror explanation must not swallow it."""
    assert is_spurious_flip("accessory", "watch on left wrist", "watch on right wrist") is False


def test_every_schema_attribute_is_classified():
    for attr in SCHEMA_ATTRIBUTES:
        assert REFERENCE[attr] in ("world", "camera")


def test_only_position_is_camera_relative():
    camera = {a for a, ref in REFERENCE.items() if ref == "camera"}
    assert camera == {"position"}


def test_anatomy_and_possessions_are_world_relative():
    for attr in ("injury", "accessory", "facial_hair", "hair", "wearing"):
        assert REFERENCE[attr] == "world"


def test_a_change_with_no_side_token_is_not_a_flip():
    """Most transitions are not about sides at all; those are the search's job to judge,
    not this filter's to touch."""
    assert is_spurious_flip("position", "seated at the table", "standing by the door") is False


def test_same_side_on_both_ends_is_not_a_flip():
    """A difference that keeps the same side is a difference in something else, not a
    mirror."""
    assert is_spurious_flip("position", "left of the bar", "left of the doorway") is False


def test_a_one_sided_change_is_not_a_flip():
    """One value names a side and the other does not — an appearance, not a mirror swap.
    There is nothing to explain away."""
    assert is_spurious_flip("position", "left of frame", "centre of frame") is False


def test_guidance_states_both_frames():
    assert "world-relative" in GUIDANCE and "camera-relative" in GUIDANCE
