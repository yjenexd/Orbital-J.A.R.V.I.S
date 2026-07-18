"""Shared in-memory test doubles for the Supabase client, extending the
db-backed FakeTable/FakeSupabase pattern used across the suite with a fake
``.rpc(...)`` (for the match_messages retrieval RPC) and an auto-incrementing
message_id on insert (so self-exclusion logic can be exercised)."""

from types import SimpleNamespace


class FakeTable:
    def __init__(self, db, name, counters):
        self._db = db
        self._name = name
        self._counters = counters
        self._filters = []
        self._limit = None
        self._single = False
        self._maybe_single = False
        self._insert_payload = None
        self._update_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self._filters.append((key, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self._limit = value
        return self

    def single(self):
        self._single = True
        return self

    def maybe_single(self):
        self._maybe_single = True
        return self

    def insert(self, payload):
        self._insert_payload = payload
        return self

    def update(self, payload):
        self._update_payload = payload
        return self

    def delete(self):
        self._update_payload = "__delete__"
        return self

    def _rows(self):
        rows = self._db.setdefault(self._name, [])
        filtered = rows
        for key, value in self._filters:
            filtered = [r for r in filtered if r.get(key) == value]
        return filtered

    def execute(self):
        if self._insert_payload is not None:
            payload = dict(self._insert_payload)
            # Auto-assign a monotonic id for tables with an *_id PK convention.
            if self._name == "messages" and "message_id" not in payload:
                self._counters["message_id"] += 1
                payload["message_id"] = self._counters["message_id"]
            self._db.setdefault(self._name, []).append(payload)
            return SimpleNamespace(data=[payload])

        if self._update_payload == "__delete__":
            rows = self._rows()
            remaining = [r for r in self._db.get(self._name, []) if r not in rows]
            self._db[self._name] = remaining
            return SimpleNamespace(data=rows)

        if self._update_payload is not None:
            rows = self._rows()
            for row in rows:
                row.update(self._update_payload)
            return SimpleNamespace(data=rows)

        rows = self._rows()
        if self._limit is not None:
            rows = rows[: self._limit]
        if self._single:
            return SimpleNamespace(data=rows[0] if rows else {})
        if self._maybe_single:
            return SimpleNamespace(data=rows[0] if rows else None)
        return SimpleNamespace(data=rows)


class FakeRpc:
    def __init__(self, handler, fn_name, params):
        self._handler = handler
        self._fn_name = fn_name
        self._params = params

    def execute(self):
        if self._handler is None:
            raise RuntimeError(f"No fake rpc handler registered for {self._fn_name}")
        return SimpleNamespace(data=self._handler(self._fn_name, self._params))


class FakeSupabase:
    def __init__(self, db, rpc_handler=None):
        self._db = db
        self._rpc_handler = rpc_handler
        self._counters = {"message_id": 1000}

    def table(self, name):
        return FakeTable(self._db, name, self._counters)

    def rpc(self, fn_name, params):
        return FakeRpc(self._rpc_handler, fn_name, params)
