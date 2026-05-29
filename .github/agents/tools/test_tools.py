"""
Test suite for Code Review Agent tools.
Run with: python -m pytest .github/agents/tools/test_tools.py
"""

import pytest
from complexity_analyzer import complexity_analyzer
from security_linter import security_linter
from codespace_file_reader import codespace_file_reader


class TestComplexityAnalyzer:
    """Tests for the complexity_analyzer tool."""
    
    def test_simple_function(self):
        """Test analysis of a simple function."""
        code = """
def add(a, b):
    return a + b
"""
        result = complexity_analyzer(code)
        
        assert 'error' not in result
        assert result['cyclomatic_complexity_max'] == 1
        assert result['maintainability_index'] > 80  # Simple code should be maintainable
        assert len(result['functions']) == 1
        assert result['functions'][0]['name'] == 'add'
    
    def test_complex_function(self):
        """Test analysis of a complex function with multiple branches."""
        code = """
def complex(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0
"""
        result = complexity_analyzer(code)
        
        assert 'error' not in result
        assert result['cyclomatic_complexity_max'] > 1
        assert result['functions'][0]['complexity'] >= 4
    
    def test_empty_code(self):
        """Test analysis of empty code."""
        result = complexity_analyzer("")
        
        assert 'error' not in result
        assert result['cyclomatic_complexity_max'] == 1
        assert len(result['functions']) == 0
    
    def test_syntax_error(self):
        """Test handling of syntax errors."""
        code = "def broken(:"
        result = complexity_analyzer(code)
        
        assert 'error' in result


class TestSecurityLinter:
    """Tests for the security_linter tool."""
    
    def test_hardcoded_password(self):
        """Test detection of hardcoded passwords."""
        code = """
password = "hardcoded_password123"
"""
        result = security_linter(code)
        
        assert 'error' not in result
        assert result['total_issues'] > 0
        # Should detect hardcoded password
        assert any('password' in issue['issue_text'].lower() for issue in result['issues'])
    
    def test_pickle_vulnerability(self):
        """Test detection of pickle deserialization vulnerability."""
        code = """
import pickle

def load_data(user_input):
    return pickle.loads(user_input)
"""
        result = security_linter(code)
        
        assert 'error' not in result
        assert result['total_issues'] > 0
        # Should detect pickle usage
        assert any('pickle' in issue['issue_text'].lower() for issue in result['issues'])
    
    def test_shell_injection(self):
        """Test detection of shell injection risk."""
        code = """
import subprocess

def run_command(user_input):
    subprocess.call(user_input, shell=True)
"""
        result = security_linter(code)
        
        assert 'error' not in result
        assert result['total_issues'] > 0
        # Should detect shell injection risk
        assert result['high_severity'] > 0 or result['medium_severity'] > 0
    
    def test_safe_code(self):
        """Test analysis of safe code."""
        code = """
def add(a, b):
    return a + b
"""
        result = security_linter(code)
        
        assert 'error' not in result
        # Safe code should have no issues (or very few low-severity)
        assert result['high_severity'] == 0


class TestCodespaceFileReader:
    """Tests for the codespace_file_reader tool."""
    
    def test_read_existing_file(self):
        """Test reading an existing file."""
        # Try to find any Python file in the workspace
        import os
        py_file = None
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.py'):
                    py_file = os.path.join(root, f)
                    break
            if py_file:
                break
        
        if not py_file:
            pytest.skip("No Python files found in workspace")
        
        result = codespace_file_reader(py_file)
        
        assert 'error' not in result
        assert result['content'] is not None
        assert result['lines'] > 0
        assert result['language'] == 'Python'
        assert result['encoding'] in ['utf-8', 'latin-1']
    
    def test_read_nonexistent_file(self):
        """Test reading a nonexistent file."""
        result = codespace_file_reader("nonexistent_file_12345.py")
        
        assert 'error' in result
        assert 'FileNotFoundError' in result['error']
    
    def test_security_boundary(self):
        """Test that path traversal is prevented."""
        result = codespace_file_reader("/etc/passwd")
        
        assert 'error' in result
        assert 'SecurityError' in result['error'] or 'outside' in result['details'].lower()
    
    def test_relative_path(self):
        """Test reading with relative path."""
        # Test with requirements.txt if it exists
        import os
        if not os.path.exists('requirements.txt'):
            pytest.skip("requirements.txt not found")
        
        result = codespace_file_reader("requirements.txt")
        
        assert 'error' not in result
        assert result['content'] is not None
    
    def test_language_detection(self):
        """Test language detection for various file types."""
        # Test Python file detection
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test(): pass")
            temp_py = f.name
        
        try:
            result = codespace_file_reader(temp_py)
            assert result.get('language') == 'Python'
        finally:
            if os.path.exists(temp_py):
                os.unlink(temp_py)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
