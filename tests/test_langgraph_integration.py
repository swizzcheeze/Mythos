import os
import json
import time

# Minimal runtime check without starting FastAPI server
from mythos_backend.mythos_graph import compile_graph, JSONFileCheckpointer


def test_revision_increment_and_persistence():
    app = compile_graph()
    session_id = "test-session-001"
    # Seed initial state
    app.update_state({"thread_id": session_id}, {
        "session_id": session_id,
        "world_name": "default",
        "style_guide": "Fantasy",
        "current_section": "Core Identity",
        "draft_content": {},
        "critique_logs": [],
        "revision_count": 0,
        "user_feedback": None,
    })
    # Provide feedback and invoke
    app.update_state({"thread_id": session_id}, {"user_feedback": "Core Identity/World Name: Eldoria"})
    app.invoke({}, config={"thread_id": session_id})

    # Check persisted state
    cp = JSONFileCheckpointer("default")
    chk = cp.get({"thread_id": session_id}) or {}
    state = chk.get("state") or {}
    assert state.get("revision_count", 0) >= 1
    assert isinstance(state.get("draft_content", {}), dict)

    # Clean up
    # Remove session from persistence
    cp.clear({"thread_id": session_id})
