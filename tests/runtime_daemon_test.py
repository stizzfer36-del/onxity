from __future__ import annotations

from onxity.kernel.identity import IdentityStore
from onxity.kernel.state import RuntimeState


def test_identity_persistence(tmp_config):
    store = IdentityStore(tmp_config)
    a = store.load_or_create()
    b = store.load_or_create()
    assert a["operator_id"] == b["operator_id"]


def test_runtime_session_lifecycle(tmp_config):
    st = RuntimeState(tmp_config)
    sess = st.start_session("ceo", {"surface": "test"})
    assert st.state["active_session_id"] == sess["id"]
    st.end_session(sess["id"])
    assert st.state["sessions"][sess["id"]]["ended_ts"] is not None
