# Code Review Agent Tools

This directory contains the custom tools used by the **Code Review Architect** agent (`mythos.CRA.agent.md`).

## Tools Overview

### 1. `complexity_analyzer.py`
Calculates quantitative code complexity metrics using the `radon` library.

**Metrics provided:**
- Cyclomatic Complexity (max and average across functions)
- Maintainability Index (0-100 scale)
- Lines of Code (LOC, LLOC, SLOC)
- Comments and blank line counts
- Halstead Difficulty metric
- Per-function complexity breakdown with rankings

**Usage:**
```python
from tools.complexity_analyzer import complexity_analyzer

code = """
def example(x):
    if x > 0:
        return x * 2
    return 0
"""

result = complexity_analyzer(code)
print(result)
```

### 2. `security_linter.py`
Performs security vulnerability analysis using the `bandit` framework.

**Detects:**
- Hardcoded passwords and secrets
- SQL injection vulnerabilities
- Command injection risks
- Insecure deserialization (pickle, yaml)
- Weak cryptography usage
- Many other OWASP-style issues

**Severity levels:** HIGH, MEDIUM, LOW

**Usage:**
```python
from tools.security_linter import security_linter

code = """
import pickle
data = pickle.loads(user_input)  # Security risk
"""

result = security_linter(code)
print(result)
```

### 3. `codespace_file_reader.py`
Safely reads files from the workspace with security sandboxing.

**Features:**
- Path traversal protection (files must be within workspace)
- File size limits (10MB max)
- Multiple encoding support (UTF-8, Latin-1, CP1252)
- Language detection by file extension
- Detailed file metadata

**Usage:**
```python
from tools.codespace_file_reader import codespace_file_reader

result = codespace_file_reader("manage.py")
print(result['content'])
```

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install radon bandit pydantic
```

## Testing

Run the test suite:
```bash
python -m pytest .github/agents/tools/test_tools.py
```

Or test individual tools:
```bash
python .github/agents/tools/complexity_analyzer.py
python .github/agents/tools/security_linter.py
python .github/agents/tools/codespace_file_reader.py
```

## Architecture

All tools follow a consistent pattern:

1. **Input validation** using type hints
2. **Pydantic models** for structured output
3. **Error handling** with descriptive error messages
4. **Deterministic results** (no LLM guessing)

## Integration with Agent

The agent (`mythos.CRA.agent.md`) orchestrates these tools:

1. User provides a file path or code block
2. Agent calls `codespace_file_reader` if needed
3. Agent calls `complexity_analyzer` and `security_linter` in parallel
4. Agent synthesizes results into a comprehensive code review report

## Security Notes

- `codespace_file_reader` prevents path traversal attacks
- All tools run in sandbox mode (no code execution)
- File size limits prevent memory exhaustion
- Temporary files are cleaned up after use
