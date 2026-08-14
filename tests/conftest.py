import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class FakeClient:
    """A stand-in for the Gemini client that returns a fixed string.

    The model calls are not what these tests are for. The parsing, the guardrails and the
    SQL are, and those are the parts that were wrong four times. A fake keeps the test
    offline and deterministic and puts the assertion on the logic instead of the network.
    """
    def __init__(self, text: str):
        self._text = text
        self.models = self

    def generate_content(self, **_kw):
        class _R:
            pass
        r = _R()
        r.text = self._text
        return r
