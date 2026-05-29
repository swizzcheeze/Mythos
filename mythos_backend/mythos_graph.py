from __future__ import annotations

"""
LangGraph v2 migration scaffold for Mythos.

Implements:
- CreationSessionState (TypedDict)
- JSONFileCheckpointer using existing file locking
- Stub nodes: generator_agent, critic_agent, human_feedback
- Compiled StateGraph with simple edge logic

Note: This is a non-functional scaffold to be wired into mythos_backend endpoints.
"""

from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict
import operator
import json
import os
import time

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser

# Reuse backend helpers via relative import (runtime-loaded in container)
try:
    from mythos_backend import (
        _get_lock_for_path, 
        _current_sessions_path, 
        ACTIVE_WORLD_NAME,
        _get_llm_for_generation,
        _get_llm_for_critique,
        _invoke_llm,
        LLM_PROVIDER
    )
except Exception:
    # Fallback for local linting; these will be available in-container
    def _get_lock_for_path(path: str):
        import threading
        return threading.Lock()
    def _current_sessions_path(world_name: str | None = None) -> str:
        return os.path.join("world_data", "sessions.json")
    ACTIVE_WORLD_NAME = "default"
    LLM_PROVIDER = "ollama"
    def _get_llm_for_generation(model=None, temperature=0.7):
        return None
    def _get_llm_for_critique(model=None, temperature=0.1):
        return None
    def _invoke_llm(llm, prompt: str) -> str:
        return ""


class CreationSessionState(TypedDict):
    # Identity
    session_id: str
    world_name: str
    style_guide: str

    # Workflow
    current_section: str
    draft_content: Dict[str, Any]

    # Agentic Loop State
    critique_logs: Annotated[List[str], operator.add]
    revision_count: int
    user_feedback: Optional[str]


class JSONFileCheckpointer(BaseCheckpointSaver):
    """Persist LangGraph state to JSON using Mythos file locks and atomic writes.

    Storage layout (v1): world_data/sessions.json single file.
    Each session_id maps to a serialized state dict.
    """

    def __init__(self, world_name: str | None = None):
        self.world_name = world_name or ACTIVE_WORLD_NAME
        self.path = _current_sessions_path(self.world_name)
        self.lock = _get_lock_for_path(self.path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def _read_all(self) -> Dict[str, Any]:
        with self.lock:
            if not os.path.exists(self.path):
                return {}
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}

    def _write_all(self, data: Dict[str, Any]) -> None:
        with self.lock:
            dir_path = os.path.dirname(self.path)
            tmp_path = None
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=dir_path, delete=False, suffix=".tmp") as tmp:
                    json.dump(data, tmp, indent=2, ensure_ascii=False)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    tmp_path = tmp.name
                os.replace(tmp_path, self.path)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

    # BaseCheckpointSaver interface
    def _extract_thread_id(self, config: Dict[str, Any]) -> Optional[str]:
        # Support both direct and configurable config shapes
        if not isinstance(config, dict):
            return None
        tid = config.get("thread_id")
        if tid:
            return tid
        conf = config.get("configurable") or {}
        return conf.get("thread_id")

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any] | None = None, channel_versions: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Save a checkpoint tuple and return an updated config.

        LangGraph v2 passes (config, checkpoint, metadata, channel_versions).
        We persist only the checkpoint.state with a timestamp and ignore advanced metadata.
        """
        thread_id = self._extract_thread_id(config)
        if not thread_id:
            return config
        # Persist the full LangGraph checkpoint structure as provided
        if isinstance(checkpoint, dict):
            payload = dict(checkpoint)
        else:
            payload = {"state": checkpoint}
        # Annotate with timestamp for debugging
        payload["updated_at"] = time.time()
        data = self._read_all()
        data[thread_id] = payload
        self._write_all(data)
        # Return config (LangGraph expects possibly updated config)
        return config

    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Load checkpoint for a given thread/session."""
        thread_id = self._extract_thread_id(config)
        if not thread_id:
            return None
        data = self._read_all()
        return data.get(thread_id)

    def clear(self, config: Dict[str, Any]) -> None:
        thread_id = self._extract_thread_id(config)
        if not thread_id:
            return
        data = self._read_all()
        if thread_id in data:
            del data[thread_id]
            self._write_all(data)

    def put_writes(self, config: Dict[str, Any], writes: Any, task_id: str) -> None:
        """Persist writes metadata (no-op for JSON file storage)."""
        # For our lightweight storage, we don't track per-task writes.
        return

    def get_next_version(self, channel_name: str, current_version: int | None = None) -> int:
        """Return next version number for a channel."""
        return (current_version or 0) + 1

    # LangGraph v2 expects get_tuple for advanced retrieval
    def get_tuple(self, config: Dict[str, Any]):
        """Return a tuple-like checkpoint with state and metadata.

        Minimal implementation returning a dict compatible with usage in tests.
        """
        chk = self.get(config)
        if chk is None:
            return None
        # Provide keys similar to BaseCheckpointSaver expectations
        # Wrap into a simple object with attribute access expected by LangGraph
        class _Tuple:
            def __init__(self, ns, cfg, chk_dict):
                self.checkpoint_ns = ns
                self.config = cfg
                self.checkpoint = chk_dict
                self.version = 1
                # Provide minimal metadata fields expected by LangGraph
                self.metadata = {"parents": {}, "step": chk_dict.get("v", -1)}
                # pending_writes may be absent; default to empty list
                self.pending_writes = chk_dict.get("pending_writes", [])
                self.parent_config = None
        return _Tuple(self.world_name, config, chk)


# --- Node implementations (stubs) ---

DEFAULT_GENERATOR_MODEL = os.getenv("MYTHOS_GENERATOR_MODEL", None)
DEFAULT_CRITIC_MODEL = os.getenv("MYTHOS_CRITIC_MODEL", None)
JSON_PARSER = JsonOutputParser()

def generator_agent(state: CreationSessionState) -> CreationSessionState:
    """
    Drafts JSON for the current_section using style_guide and (optional) user_feedback.

    Reads: style_guide, current_section, user_feedback, draft_content, revision_count
    Modifies: draft_content, revision_count
    LLM: ChatOllama (format=json) [wired in full impl]
    """
    draft = state.get("draft_content", {})
    section = state.get("current_section", "core")
    feedback = state.get("user_feedback")
    style = state.get("style_guide", "Fantasy")
    prompt = (
        "You are a creative worldbuilding assistant. Produce STRICT JSON for the requested section.\n"
        f"Section: {section}\n"
        f"Style guide: {style}\n"
        "Rules: Return ONLY JSON. Do not include explanations.\n"
        "JSON Keys: Use concise keys relevant to the section (e.g., 'World Name', 'Central Theme').\n"
        "If user feedback is provided, incorporate it immediately.\n"
        f"User feedback: {feedback if feedback else '(none)'}\n"
    )
    try:
        llm = _get_llm_for_generation(model=DEFAULT_GENERATOR_MODEL, temperature=0.7)
        content = _invoke_llm(llm, prompt)
        try:
            parsed = JSON_PARSER.parse(content)
        except Exception:
            # Fallback: attempt json.loads; else wrap as note
            import json as _json
            try:
                parsed = _json.loads(content)
            except Exception:
                parsed = {"note": content}
        draft[section] = parsed
    except Exception as e:
        # Fallback to simple echo behavior if model fails
        draft[section] = feedback or {"note": f"Draft for {section} in style {style}"}
        # Include failure info for transparency
        logs = list(state.get("critique_logs", []))
        logs.append(f"Generator fallback due to error: {e}")
        state["critique_logs"] = logs
    state["draft_content"] = draft
    state["revision_count"] = int(state.get("revision_count", 0)) + 1
    return state


def critic_agent(state: CreationSessionState) -> Dict[str, Any]:
    """
    Critiques the latest draft against the style guide.

    Reads: draft_content, style_guide, revision_count
    Modifies: critique_logs
    LLM: ChatOllama (text/json) [wired in full impl]
    """
    logs = list(state.get("critique_logs", []))
    style = state.get("style_guide", "Fantasy")
    section = state.get("current_section", "core")
    content = (state.get("draft_content", {}) or {}).get(section)
    prompt = (
        "You are a senior editor. Evaluate the draft content against the style guide.\n"
        f"Style: {style}\n"
        f"Section: {section}\n"
        "Decision: Return STRICT JSON with keys { 'decision': 'approve'|'reject', 'feedback': string, 'score': number }.\n"
        "Criteria: If score >= 8, approve. Otherwise reject with actionable feedback.\n"
        f"Draft: {content}\n"
    )
    try:
        llm = _get_llm_for_critique(model=DEFAULT_CRITIC_MODEL, temperature=0.1)
        text = _invoke_llm(llm, prompt)
        try:
            data = JSON_PARSER.parse(text)
        except Exception:
            import json as _json
            try:
                data = _json.loads(text)
            except Exception:
                data = {"decision": "approve", "feedback": "Parser fallback: approving.", "score": 8.0}
        decision = data.get("decision", "approve")
        feedback = data.get("feedback", "Looks good.")
        score = float(data.get("score", 8.0))
        rc = int(state.get("revision_count", 0))
        if rc >= 3 and decision == "reject":
            decision = "approve"
            feedback = f"Auto-approve at max revisions. Prior feedback: {feedback}"
        logs.append(feedback)
        state["critique_logs"] = logs
        return {"decision": decision, "score": score}
    except Exception as e:
        logs.append(f"Critic fallback due to error: {e}")
        state["critique_logs"] = logs
        return {"decision": "approve", "score": 8.0}


def human_feedback(state: CreationSessionState) -> CreationSessionState:
    """
    No-op human node to allow MCP to provide updates via API.

    Reads: user_feedback
    Modifies: none
    """
    return state


# --- Graph compilation ---

def compile_graph(world_name: str | None = None):
    g = StateGraph(CreationSessionState)
    g.add_node("generator", generator_agent)
    g.add_node("critic", critic_agent)
    g.add_node("human", human_feedback)

    # Default entry
    g.set_entry_point("generator")

    # Edge logic
    def should_revise(state: CreationSessionState, result: Dict[str, Any]):
        decision = result.get("decision")
        if decision == "reject":
            return "generator"
        return "human"

    g.add_edge("generator", "critic")
    g.add_conditional_edges("critic", should_revise)
    g.add_edge("human", END)

    checkpointer = JSONFileCheckpointer(world_name)
    app = g.compile(checkpointer=checkpointer)
    return app


__all__ = [
    "CreationSessionState",
    "JSONFileCheckpointer",
    "compile_graph",
]
