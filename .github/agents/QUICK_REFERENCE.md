# 📋 Code Review Agent - Quick Reference

## 🎯 Agent Overview

**Name:** code-reviewer  
**Type:** Static Code Analysis & Security Review  
**Target:** VS Code / GitHub Copilot  
**Status:** ✅ Fully Implemented  

## 🛠️ Three Custom Tools

| Tool | Purpose | Library | Output |
|------|---------|---------|--------|
| `codespace_file_reader` | Safe file reading with sandboxing | Native Python | File content + metadata |
| `complexity_analyzer` | Code complexity metrics | `radon` | CC, MI, LOC, Halstead |
| `security_linter` | Security vulnerability detection | `bandit` | Vulnerabilities by severity |

## ⚡ Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run demo on a file
python .github/agents/tools/demo.py manage.py

# Run all tests
python -m pytest .github/agents/tools/test_tools.py -v

# Test individual tools
python .github/agents/tools/complexity_analyzer.py
python .github/agents/tools/security_linter.py
python .github/agents/tools/codespace_file_reader.py
```

## 📊 Metrics at a Glance

### Cyclomatic Complexity
- **1-5**: Simple ✅
- **6-10**: Moderate ⚠️
- **11-20**: High 🔴
- **21+**: Very High 🚨 Refactor!

### Maintainability Index
- **100-80**: Excellent ✅
- **79-50**: Good ⚠️
- **49-20**: Poor 🔴
- **19-0**: Critical 🚨

### Security Severity
- **HIGH**: Fix immediately 🚨
- **MEDIUM**: Address soon ⚠️
- **LOW**: Best practice 💡

## 🎯 Quality Score Formula

```
Score = 100
  - (100 - Maintainability_Index) × 0.3
  - (Max_Complexity - 10) × 2
  - High_Severity_Issues × 20
  - Medium_Severity_Issues × 10
  - Low_Severity_Issues × 2
```

## 🔒 Security Checks

✅ Hardcoded passwords/secrets  
✅ SQL injection risks  
✅ Command injection  
✅ Insecure deserialization (pickle/yaml)  
✅ Weak cryptography  
✅ Path traversal vulnerabilities  
✅ 50+ additional OWASP patterns  

## 📁 File Structure

```
.github/agents/
├── mythos.CRA.agent.md          # Agent config
├── README.md                     # This overview
├── SETUP_GUIDE.md               # Detailed setup
├── ARCHITECTURE.md              # System design
└── tools/
    ├── complexity_analyzer.py   # Tool #1
    ├── security_linter.py       # Tool #2
    ├── codespace_file_reader.py # Tool #3
    ├── demo.py                  # Full workflow
    └── test_tools.py            # Test suite
```

## 🚀 Usage Patterns

### Pattern 1: Analyze Single File
```bash
python .github/agents/tools/demo.py path/to/file.py
```

### Pattern 2: Use in Python Script
```python
from tools import complexity_analyzer, security_linter

code = open('my_file.py').read()
metrics = complexity_analyzer(code)
security = security_linter(code)
```

### Pattern 3: CI/CD Integration
```bash
# In your CI pipeline
find . -name "*.py" -exec \
  python .github/agents/tools/demo.py {} \; \
  | tee code_review_report.txt
```

## 🎨 Example Output Structure

```
1. 📂 File Metadata
   - Path, lines, size, language

2. 📊 Complexity Metrics
   - CC (max/avg), MI, LOC, functions

3. 🔒 Security Scan
   - Issue count by severity
   - Detailed vulnerability list

4. 📋 Report
   - Overall score (0-100)
   - Critical issues (security HIGH)
   - Major issues (complexity + security MEDIUM)
   - Minor issues (security LOW)
   - Actionable recommendations
```

## 🔑 Key Features

✨ **No Code Execution** - Pure static analysis  
✨ **Workspace Sandboxed** - File access restricted  
✨ **Parallel Processing** - Fast analysis  
✨ **Structured Output** - JSON-compatible  
✨ **Error Resilient** - Graceful failure handling  

## 📦 Dependencies

```bash
radon~=6.0.1      # Complexity analysis
bandit~=1.7.10    # Security scanning
pydantic~=2.10.5  # Data validation
pytest~=8.0.0     # Testing (optional)
```

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | `export PYTHONPATH="${PYTHONPATH}:.github/agents"` |
| "Unknown tool" warning | Expected until agent registered with Copilot |
| Permission denied | `chmod +x .github/agents/tools/demo.py` |
| Module not found | `pip install -r requirements.txt` |

## 🎓 Learn More

- **Detailed Setup**: See `SETUP_GUIDE.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Tool Docs**: See `tools/README.md`
- **Tests**: Run `test_tools.py`

## 📞 Quick Help

```bash
# Check if tools are working
python -c "from tools import *; print('✅ All tools loaded')"

# Verify dependencies
pip list | grep -E "radon|bandit|pydantic"

# Show file structure
ls -R .github/agents/
```

---

**Status**: ✅ Ready to use  
**Version**: 1.0.0  
**Last Updated**: December 3, 2025  
