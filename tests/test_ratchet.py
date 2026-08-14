"""The earned-autonomy ledger (spec §9.5). Deterministic and offline: authority is a
function of the recorded history, so no model and no clock enter here.

Every assertion is on `authority_of` — the derived end state — never on a return value
treated as a label, because the property under test is what a class is *allowed to do*,
not what the ledger said while getting there.
"""
from continuity.ratchet import Authority, Ledger


def test_a_streak_of_clean_calls_earns_provisional():
    """N confirmed-clean calls, and not one fewer, lift a class out of SHADOW."""
    led = Ledger(n=5)
    for _ in range(4):
        led.record("accessory-swap", accepted=True)
    assert led.authority_of("accessory-swap") == Authority.SHADOW  # four is not five
    led.record("accessory-swap", accepted=True)
    assert led.authority_of("accessory-swap") == Authority.PROVISIONAL


def test_one_rejected_flag_demotes_a_rung():
    """A false alarm a human throws out costs the class a rung at once — the expensive
    failure on a set, so it is the one that moves authority the fastest."""
    led = Ledger(n=5)
    for _ in range(5):
        led.record("injury-moved", accepted=True)
    assert led.authority_of("injury-moved") == Authority.PROVISIONAL
    led.record("injury-moved", accepted=False)
    assert led.authority_of("injury-moved") == Authority.SHADOW


def test_a_rung_is_re_earned_from_scratch_after_a_rejection():
    """The streak is spent by the rejection, so the next promotion needs the full N again;
    a class cannot bounce back on a single good call after misfiring."""
    led = Ledger(n=3, m=3)
    for _ in range(3):
        led.record("hat-swap", accepted=True)
    led.record("hat-swap", accepted=False)  # back to SHADOW, streak reset
    led.record("hat-swap", accepted=True)
    assert led.authority_of("hat-swap") == Authority.SHADOW  # one is not three
    for _ in range(2):
        led.record("hat-swap", accepted=True)
    assert led.authority_of("hat-swap") == Authority.PROVISIONAL


def test_classes_earn_authority_independently():
    """One class reaching the floor must not move another; the ledger keyed the streak by
    class or a single bad film would switch everything off."""
    led = Ledger(n=5)
    for _ in range(5):
        led.record("a", accepted=True)
    assert led.authority_of("a") == Authority.PROVISIONAL
    assert led.authority_of("b") == Authority.SHADOW  # never confirmed, stays silent


def test_restrict_clamps_down_and_can_never_raise():
    led = Ledger(n=5, m=5)
    for _ in range(10):  # N to PROVISIONAL, M more to LIVE
        led.record("accessory-swap", accepted=True)
    assert led.authority_of("accessory-swap") == Authority.LIVE

    led.restrict("accessory-swap", Authority.SHADOW)
    assert led.authority_of("accessory-swap") == Authority.SHADOW

    # Naming a higher level does not lift it: the clamp door only closes.
    led.restrict("accessory-swap", Authority.LIVE)
    assert led.authority_of("accessory-swap") == Authority.SHADOW


def test_restrict_to_a_higher_level_is_a_no_op():
    """Restrict is not a setter. A class at PROVISIONAL asked to 'restrict to LIVE' stays
    where it earned, because the only path that raises authority is a clean-call streak."""
    led = Ledger(n=5)
    for _ in range(5):
        led.record("injury-moved", accepted=True)
    led.restrict("injury-moved", Authority.LIVE)
    assert led.authority_of("injury-moved") == Authority.PROVISIONAL


def test_the_authority_order_is_shadow_below_provisional_below_live():
    assert Authority.SHADOW < Authority.PROVISIONAL < Authority.LIVE


def test_the_ledger_exposes_no_way_to_delete_or_amend():
    """The append-only guarantee is the public surface: record, authority_of, restrict and
    nothing that could rewrite history. If a mutation method is ever added, this fails."""
    public = {name for name in dir(Ledger) if not name.startswith("_")}
    assert public == {"record", "authority_of", "restrict"}
