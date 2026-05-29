# Code Review Agent Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Copilot / VS Code                     │
│                                                                   │
│  User: "@code-reviewer analyze hello_world/core/views.py"       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              mythos.CRA.agent.md (Agent Persona)                 │
│                                                                   │
│  • Orchestrates tool calls                                       │
│  • Synthesizes results                                           │
│  • Generates comprehensive report                                │
└─────────────────┬───────────────────┬──────────────┬────────────┘
                  │                   │              │
                  ▼                   ▼              ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐
    │ Tool #1         │  │ Tool #2          │  │ Tool #3       │
    │ File Reader     │  │ Complexity       │  │ Security      │
    │                 │  │ Analyzer         │  │ Linter        │
    └─────────────────┘  └──────────────────┘  └───────────────┘
           │                     │                     │
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐
    │ Reads files     │  │ Calculates:      │  │ Detects:      │
    │ from workspace  │  │ • Cyclomatic CC  │  │ • SQL Inj.    │
    │ with sandboxing │  │ • Maintainability│  │ • Hardcoded   │
    │                 │  │ • LOC metrics    │  │   secrets     │
    │ Returns:        │  │ • Halstead       │  │ • Pickle use  │
    │ • Content       │  │                  │  │ • Shell Inj.  │
    │ • Metadata      │  │ Returns:         │  │               │
    │ • Language      │  │ • Metrics dict   │  │ Returns:      │
    │                 │  │ • Function list  │  │ • Issue list  │
    └─────────────────┘  └──────────────────┘  └───────────────┘
```

## Data Flow

### 1. Input Phase
```
User Request → Agent receives file path or code block
```

### 2. Execution Phase (Parallel)
```
┌─────────────────────────────────────────────────────────────┐
│ If file path provided:                                      │
│   codespace_file_reader(filepath) → file_content           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Parallel Analysis:                                          │
│   complexity_analyzer(code) → metrics                       │
│   security_linter(code) → vulnerabilities                   │
└─────────────────────────────────────────────────────────────┘
```

### 3. Synthesis Phase
```
Agent combines:
  • File metadata
  • Complexity metrics
  • Security findings
  • LLM reasoning

         ↓

Generates structured report:
  • Summary scorecard
  • Critical issues (security)
  • Major issues (complexity, maintainability)
  • Minor issues (style, optimization)
  • Recommendations (prioritized actions)
```

## Tool Details

### codespace_file_reader.py
```python
Input:  filepath (str)
Output: {
    "filepath": str,
    "content": str,
    "lines": int,
    "size_bytes": int,
    "encoding": str,
    "language": str
}

Security:
  ✓ Path traversal protection
  ✓ Workspace sandboxing
  ✓ File size limits (10MB)
  ✓ Multiple encoding support
```

### complexity_analyzer.py
```python
Input:  code (str)
Output: {
    "cyclomatic_complexity_max": int,
    "cyclomatic_complexity_avg": float,
    "maintainability_index": float,
    "loc": int,
    "lloc": int,
    "sloc": int,
    "comments": int,
    "blank": int,
    "halstead_difficulty": float,
    "functions": [
        {
            "name": str,
            "complexity": int,
            "line_number": int,
            "rank": str  # A-F
        }
    ]
}

Library: radon
```

### security_linter.py
```python
Input:  code (str), filename (str, optional)
Output: {
    "total_issues": int,
    "high_severity": int,
    "medium_severity": int,
    "low_severity": int,
    "issues": [
        {
            "severity": str,      # HIGH/MEDIUM/LOW
            "confidence": str,
            "issue_text": str,
            "test_id": str,       # e.g., B301
            "test_name": str,
            "line_number": int,
            "code": str,
            "more_info": str      # Documentation URL
        }
    ],
    "metrics": dict
}

Library: bandit
Checks: 50+ security patterns
```

## Agent Decision Tree

```
Start: User provides input
    │
    ├─ Is it a file path?
    │   ├─ Yes → Call codespace_file_reader
    │   │         ├─ Success? → Continue with code
    │   │         └─ Error? → Return error report
    │   │
    │   └─ No → Use code block directly
    │
    ├─ Call complexity_analyzer (parallel)
    │   └─ Store metrics
    │
    ├─ Call security_linter (parallel)
    │   └─ Store vulnerabilities
    │
    ├─ Calculate overall score:
    │   score = 100
    │   score -= (100 - MI) * 0.3
    │   score -= (CC_max - 10) * 2
    │   score -= high_severity * 20
    │   score -= medium_severity * 10
    │   score -= low_severity * 2
    │
    └─ Generate report:
        ├─ Summary scorecard
        ├─ Critical issues (high severity security)
        ├─ Major issues (complexity + medium security)
        ├─ Minor issues (low severity security)
        └─ Recommendations (prioritized actions)
```

## Example Scoring

```
Base Score: 100

Deductions:
  - Low Maintainability (MI=45):    -16.5  (100-45)*0.3
  - High Complexity (CC=18):        -16    (18-10)*2
  - 1 High Security Issue:          -20
  - 2 Medium Security Issues:       -20
  - 3 Low Security Issues:          -6
                                    -----
Final Score:                         21.5  (Failing)

Grade Scale:
  90-100: Excellent
  70-89:  Good
  50-69:  Needs Improvement
  0-49:   Poor (Requires Refactoring)
```

## Integration Points

### GitHub Copilot Chat
```
@code-reviewer review src/auth.py
@code-reviewer analyze this function: [paste code]
```

### CI/CD Pipeline
```bash
python .github/agents/tools/demo.py src/**/*.py > review_report.txt
```

### VS Code Commands
```json
{
  "command": "code-reviewer.analyze",
  "title": "Analyze with Code Review Agent"
}
```

## Dependencies

```
Runtime:
  - Python 3.8+
  - radon 6.0.1
  - bandit 1.7.10
  - pydantic 2.10.5

Optional:
  - pytest 8.0.0 (testing)
```

## Performance Characteristics

```
File Reading:        < 100ms  (for files < 1MB)
Complexity Analysis: < 500ms  (for files < 1000 LOC)
Security Scan:       < 1s     (for files < 1000 LOC)
Total Analysis:      < 2s     (typical file)
```

## Error Handling

All tools follow consistent error pattern:
```python
{
    "error": "ErrorType: Brief message",
    "details": "Detailed explanation of what went wrong"
}
```

Common errors:
- FileNotFoundError
- SecurityError (path traversal)
- EncodingError
- FileTooLargeError
- SyntaxError (invalid Python code)
