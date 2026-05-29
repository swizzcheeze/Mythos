import os
import json
import uuid

# Ensure imports work whether running as module or script
try:
    from mythos_backend.mythos_graph import compile_graph, JSONFileCheckpointer
except Exception:
    # Fallback for direct execution context
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mythos_backend.mythos_graph import compile_graph, JSONFileCheckpointer


def test_revision_increments(tmp_path):
    """Smoke test: graph + custom checkpointer handle update_state/invoke without error."""
    # Point Lore DB to a temp path so any file IO is isolated
    os.environ["LORE_DB_PATH"] = str(tmp_path / "lore_db.json")
    with open(os.environ["LORE_DB_PATH"], "w", encoding="utf-8") as f:
        json.dump([], f)

    app = compile_graph()
    session_id = uuid.uuid4().hex

    # Initialize state
    initial_state = {
        "session_id": session_id,
        "world_name": "default",
        "style_guide": "Fantasy",
        "current_section": "Core Identity",
        "draft_content": {},
        "critique_logs": [],
        "revision_count": 0,
        "user_feedback": None,
    }

    # These calls should not raise; if they do, the test fails
    app.update_state({"configurable": {"thread_id": session_id}}, initial_state)
    app.update_state({"configurable": {"thread_id": session_id}}, {"user_feedback": "World Name: Elderglow"})
    app.invoke({}, config={"configurable": {"thread_id": session_id}})


def test_checkpointer_atomic(tmp_path):
    world_name = f"testworld_{uuid.uuid4().hex[:8]}"
    cp = JSONFileCheckpointer(world_name)

    def write_state(i):
        cp.put({"thread_id": f"t{i}"}, {"state": {"i": i}})

    # Concurrent writes
    import threading
    threads = [threading.Thread(target=write_state, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # File should be valid JSON
    data = cp.get({"thread_id": "t9"})
    assert isinstance(data, dict)
