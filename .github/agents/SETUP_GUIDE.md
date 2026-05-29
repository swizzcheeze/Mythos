# Code Review Agent - Setup & Usage Guide

## 🎯 Overview

The **Code Review Architect** agent has been successfully created with three custom tools for comprehensive static code analysis:

1. **complexity_analyzer** - Measures code complexity metrics
2. **security_linter** - Detects security vulnerabilities
3. **codespace_file_reader** - Safely reads workspace files

## 📁 File Structure

```
.github/agents/
├── mythos.CRA.agent.md          # Agent configuration and persona
└── tools/
    ├── __init__.py               # Package initialization
    ├── complexity_analyzer.py    # Complexity metrics tool
    ├── security_linter.py        # Security analysis tool
    ├── codespace_file_reader.py  # File reader with sandboxing
    ├── demo.py                   # Complete workflow demonstration
    ├── test_tools.py             # Test suite
    └── README.md                 # Tools documentation
```

## 🚀 Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install the specific packages:

```bash
pip install radon bandit pydantic
```

### Step 2: Verify Installation

Test each tool individually:

```bash
# Test complexity analyzer
python .github/agents/tools/complexity_analyzer.py

# Test security linter
python .github/agents/tools/security_linter.py

# Test file reader
python .github/agents/tools/codespace_file_reader.py
```

## 💻 Usage

### Using the Demo Script

The demo script shows the complete agent workflow:

```bash
# Review a specific file
python .github/agents/tools/demo.py manage.py

# Review default files
python .github/agents/tools/demo.py
```

### Using Individual Tools

#### Complexity Analyzer

```python
from tools.complexity_analyzer import complexity_analyzer

code = """
def complex_function(x, y):
    if x > 0:
        if y > 0:
            return x + y
    return 0
"""

result = complexity_analyzer(code)
print(f"Max Complexity: {result['cyclomatic_complexity_max']}")
print(f"Maintainability: {result['maintainability_index']}/100")
```

#### Security Linter

```python
from tools.security_linter import security_linter

code = """
import pickle
password = "hardcoded_pass123"
data = pickle.loads(user_input)
"""

result = security_linter(code)
print(f"Total Issues: {result['total_issues']}")
print(f"High Severity: {result['high_severity']}")
```

#### File Reader

```python
from tools.codespace_file_reader import codespace_file_reader

result = codespace_file_reader("manage.py")
if 'error' not in result:
    print(f"Lines: {result['lines']}")
    print(f"Language: {result['language']}")
```

## 🧪 Running Tests

```bash
# Install pytest if needed
pip install pytest

# Run the test suite
python -m pytest .github/agents/tools/test_tools.py -v
```

## 🤖 Using the Agent

Once configured, you can invoke the code reviewer agent in GitHub Copilot:

```
@code-reviewer please review hello_world/core/views.py
```

or

```
@code-reviewer analyze this code:
def insecure_function(user_input):
    eval(user_input)
```

The agent will:
1. Read the file (if path provided)
2. Analyze complexity metrics
3. Scan for security vulnerabilities
4. Generate a comprehensive report with:
   - Summary scorecard
   - Critical/Major/Minor issues
   - Actionable recommendations

## 📊 Example Output

```
🔍 Starting code review for: manage.py

📂 Step 1: Reading file...
   ✓ Read 22 lines (664 bytes)
   ✓ Language: Python

📊 Step 2: Analyzing code complexity...
   ✓ Max Cyclomatic Complexity: 3
   ✓ Maintainability Index: 72.4/100
   ✓ Logical Lines of Code: 15

🔒 Step 3: Running security scan...
   ✓ Total issues found: 0
   ✓ HIGH severity: 0
   ✓ MEDIUM severity: 0
   ✓ LOW severity: 0

================================================================================
📋 CODE REVIEW SUMMARY REPORT
================================================================================

🎯 Overall Quality Score: 92/100
   File: manage.py
   Lines: 22
   Language: Python

🚨 CRITICAL ISSUES
   ✓ No critical security issues detected

⚠️  MAJOR ISSUES
   ✓ No major issues detected

💡 MINOR ISSUES & SUGGESTIONS
   ✓ No minor issues detected

✅ RECOMMENDATIONS
   ✓ Code meets all quality standards!
```

## 🔒 Security Features

- **Sandboxing**: File reader prevents path traversal attacks
- **No Code Execution**: All analysis is static (no eval/exec)
- **File Size Limits**: 10MB maximum to prevent memory exhaustion
- **Clean Error Handling**: Graceful failures with descriptive messages

## 📈 Metrics Reference

### Cyclomatic Complexity
- **1-5**: Simple, low risk
- **6-10**: Moderate complexity
- **11-20**: High complexity, consider refactoring
- **21+**: Very high complexity, hard to test

### Maintainability Index
- **100-80**: Highly maintainable
- **79-50**: Moderately maintainable
- **49-20**: Difficult to maintain
- **19-0**: Very difficult to maintain

### Security Severity
- **HIGH**: Critical vulnerabilities requiring immediate attention
- **MEDIUM**: Important issues that should be addressed
- **LOW**: Minor issues or best practice violations

## 🛠️ Troubleshooting

### Import Errors

If you get import errors, ensure you're in the correct directory:

```bash
cd /workspaces/codespaces-django
export PYTHONPATH="${PYTHONPATH}:.github/agents"
```

### Tool Not Found Errors

The agent configuration shows "Unknown tool" warnings until the tools are properly registered with the GitHub Copilot system. This is expected during development.

### Dependency Issues

Ensure all packages are installed:

```bash
pip list | grep -E "radon|bandit|pydantic"
```

## 📚 Additional Resources

- [Radon Documentation](https://radon.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [GitHub Copilot Agents](https://docs.github.com/en/copilot/using-github-copilot/using-extensions/using-github-copilot-extensions)

## 🎓 Next Steps

1. Install dependencies
2. Run the demo script to see the workflow
3. Test with your own code files
4. Integrate with your CI/CD pipeline
5. Customize thresholds in the agent persona

Enjoy comprehensive code reviews! 🚀
