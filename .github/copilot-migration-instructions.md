MYTHOS v2: LangGraph Architecture & Agentic Workflow

Architecture Overview

Objective: Refactor mythos_backend from passive state machines to an Agentic Cyclic Graph using LangGraph.
Hardware Target: NVIDIA RTX 3090 (24GB VRAM). Optimization for context window and model loading is critical.
Orchestration: LangGraph StateGraph running on a local FastAPI backend.

Data Flow:
LM Studio (User) → MCP Tool Call (session_update) → FastAPI → LangGraph Node (Resume) → LLM (Ollama) → JSON Checkpointer → Persistent Storage.

Critical Patterns

1. The "MCP-Driven Human Node"

Unlike standard LangGraph web examples where interrupt_before=["human"] halts for console input, our "Human" is an API client (LM Studio).

Pattern: The graph must have a human_feedback node that does nothing (pass).

Mechanism:

The graph pauses at human_feedback.

The API endpoint mythos_creation_session_update receives a payload.

The endpoint updates the graph state (update_state) with the user's input.

The endpoint calls graph.invoke(..., config=thread_config) to resume execution.

2. Custom JSON Persistence (No Databases)

We strictly avoid Postgres/SQLite to maintain portability. You must implement a custom Checkpointer.

Class: JSONFileCheckpointer inheriting from BaseCheckpointSaver.

Constraint: Must use the existing atomic locking mechanism from mythos_backend.py (_get_lock_for_path).

Storage: Maps thread_id (session_id) to the serialized state in world_data/sessions.json.

3. VRAM Optimization (RTX 3090)

Model Loading: Use keep_alive="5m" in ChatOllama to prevent the model from unloading between the "Draft" and "Critique" nodes. Unloading/reloading destroys the interactive feel.

Context Management: The State object accumulates history. Use trim_messages or manual pruning in the critique_node if critique_logs exceed 10 entries.

The LangGraph Blueprint

1. State Definition (Strict Pydantic)

from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict
import operator

class CreationSessionState(TypedDict):
    # Identity
    session_id: str
    world_name: str
    style_guide: str    # e.g., "Gothic Horror"
    
    # Workflow
    current_section: str        # e.g., "geography"
    draft_content: Dict[str, Any] # The evolving output
    
    # Agentic Loop State
    critique_logs: Annotated[List[str], operator.add] # History of pushback
    revision_count: int         # Safety valve (max 3 loops)
    user_feedback: Optional[str] # Injection point for MCP


2. Node Architecture

Node A: generator_agent

LLM: ChatOllama(format="json", ...)

Input: style_guide, current_section, user_feedback.

Logic:

If user_feedback exists, incorporate it immediately.

Generate the JSON field for current_section.

Output: Updates draft_content and increments revision_count.

Node B: critic_agent

LLM: ChatOllama (Text mode is fine, or JSON for structured critique).

Role: The "Gatekeeper".

Prompt: "You are a senior editor. Does this draft match the '{style_guide}' style? Be harsh but constructive."

Logic:

If score > 8/10: Return "approve".

If score < 8/10: Return "reject" + specific feedback in critique_logs.

Hard Stop: If revision_count >= 3, force "approve" to prevent infinite loops.

3. Edge Logic

should_revise:

If critic == "approve" $\rightarrow$ human_feedback (Wait for next user command).

If critic == "reject" $\rightarrow$ generator_agent (Loop with critique history).

Coding Standards & Mandates

Documentation (Strict)

Every Node function must have a docstring detailing:

In: Which State keys are read.

Out: Which State keys are modified.

LLM: Which model alias is used.

Example:

def critic_node(state: CreationSessionState) -> Command[Literal["generator", "human"]]:
    """
    Evaluates the latest draft against the style guide.
    
    Reads: draft_content, style_guide, revision_count
    Modifies: critique_logs
    """


Error Handling

Ollama Timeouts: Wrap all LLM calls in try/except. If the local model hangs, return a fallback "Manual Entry Required" state rather than crashing the API.

JSON Repair: Use langchain_core.output_parsers.JsonOutputParser which handles minor JSON syntax errors from smaller models (like Llama 3 8B).

Implementation Checklist for Copilot

[ ] mythos_graph.py:

Define CreationSessionState.

Implement JSONFileCheckpointer (using mythos_backend locks).

Define Nodes (generator, critic, human).

Compile the StateGraph.

[ ] mythos_backend.py Integration:

Import the compiled graph.

Refactor mythos_creation_session_start to initialize a new Thread.

Refactor mythos_creation_session_update to graph.update_state() then graph.invoke().

[ ] Testing:

Verify revision_count increments correctly.

Verify world_data/sessions.json updates atomically after every node transition.