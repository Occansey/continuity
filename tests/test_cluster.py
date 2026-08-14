"""The direct ClickHouse path: how the store is loaded and how the web app runs the fixed
query. No real cluster — a fake client records what insert was handed and returns canned rows
from query. The assertion is on the columns and the row that reached the client, and on the
dicts query_transitions built back out, because a wrong column order or a mis-zipped result is
exactly the silent kind of bug this project keeps meeting in the pipeline rather than the unit.
"""
import continuity.cluster as cluster
from continuity.cluster import insert, query_transitions


class FakeResult:
    """Stands in for a clickhouse_connect QueryResult: column names and result rows, the two
    fields query_transitions zips together."""
    def __init__(self, column_names, result_rows):
        self.column_names = column_names
        self.result_rows = result_rows


class FakeClient:
    """Records every call instead of touching a database. `command` returns canned answers by
    call order; `insert` stashes its arguments; `query` returns a fixed FakeResult."""
    def __init__(self, command_returns=None, query_result=None):
        self._command_returns = list(command_returns or [])
        self._query_result = query_result
        self.commands = []
        self.inserts = []
        self.queries = []

    def command(self, sql):
        self.commands.append(sql)
        return self._command_returns.pop(0) if self._command_returns else None

    def insert(self, table, data, column_names=None):
        self.inserts.append({"table": table, "data": data, "column_names": column_names})

    def query(self, sql):
        self.queries.append(sql)
        return self._query_result


COLUMNS = ["work", "shot", "t", "entity", "entity_kind", "attribute", "value",
           "confidence", "source", "quote", "slot", "scene", "story_order"]


def test_insert_passes_all_thirteen_columns_in_order():
    c = FakeClient()
    n = insert(c, [{"shot": 3, "t": 1.5, "entity": "Al", "entity_kind": "person",
                    "attribute": "wearing", "value": "hat", "confidence": 0.8,
                    "source": "image", "quote": "q", "slot": "hat",
                    "scene": 2, "story_order": 4}], "detour")
    assert n == 1
    assert len(c.inserts) == 1
    call = c.inserts[0]
    assert call["table"] == "assertions"
    assert call["column_names"] == COLUMNS
    # The row must line up positionally with the columns, with work first and the numeric
    # fields coerced to their types.
    assert call["data"][0] == ["detour", 3, 1.5, "Al", "person", "wearing", "hat",
                               0.8, "image", "q", "hat", 2, 4]


def test_insert_defaults_fill_missing_fields():
    """A sparse assertion must not shift the columns. Missing numerics default and stay in
    their slot rather than dropping out and sliding everything left."""
    c = FakeClient()
    insert(c, [{"entity": "Vera"}], "w")
    row = c.inserts[0]["data"][0]
    assert row[0] == "w" and row[3] == "Vera"
    assert row[1] == -1 and row[11] == -1 and row[12] == -1   # shot, scene, story_order
    assert isinstance(row[2], float) and isinstance(row[7], float)  # t, confidence
    assert len(row) == len(COLUMNS)


def test_a_value_with_an_apostrophe_is_passed_as_data_not_sql():
    """The store path escapes quotes by string-building; this path must not, because it hands
    values to the client as parameter data. An apostrophe has to arrive intact in the row, so
    it is a value and never a fragment of SQL that could truncate the insert."""
    c = FakeClient()
    insert(c, [{"entity": "Al", "value": "Haskell's coat"}], "w")
    row = c.inserts[0]["data"][0]
    assert row[6] == "Haskell's coat"   # value column, apostrophe intact
    # It travels as data, not baked into any command string.
    assert all("Haskell's coat" not in cmd for cmd in c.commands)


def test_query_transitions_maps_rows_to_dicts_by_column_name(monkeypatch):
    """The window's columns come back paired with their values by position; a dict built from
    the wrong zip is the failure mode. Feed a canned result and assert the mapping."""
    cols = ["entity", "value_from", "value_to", "scene_from", "scene"]
    rows = [("Vera", "hoop", "stud", 5, 6), ("Al", "hat", "cap", 0, 1)]
    fake = FakeClient(command_returns=[None, "0"], query_result=FakeResult(cols, rows))
    # query_transitions builds its own client; swap in the fake so nothing dials a cluster.
    monkeypatch.setattr(cluster, "client", lambda: fake)

    out = query_transitions([{"entity": "Vera"}], "w")
    assert out == [
        {"entity": "Vera", "value_from": "hoop", "value_to": "stud",
         "scene_from": 5, "scene": 6},
        {"entity": "Al", "value_from": "hat", "value_to": "cap",
         "scene_from": 0, "scene": 1},
    ]


def test_query_transitions_loads_only_when_the_work_is_absent(monkeypatch):
    """The load is idempotent: a count of zero means insert, a nonzero count means skip. Assert
    the end state — whether insert actually ran — not the branch that was meant to run it."""
    fake_empty = FakeClient(command_returns=[None, "0"],
                            query_result=FakeResult(["entity"], []))
    monkeypatch.setattr(cluster, "client", lambda: fake_empty)
    query_transitions([{"entity": "Al"}], "w")
    assert len(fake_empty.inserts) == 1   # count was 0, so it loaded

    fake_full = FakeClient(command_returns=[None, 7],
                           query_result=FakeResult(["entity"], []))
    monkeypatch.setattr(cluster, "client", lambda: fake_full)
    query_transitions([{"entity": "Al"}], "w")
    assert fake_full.inserts == []        # count was 7, so it did not reload
