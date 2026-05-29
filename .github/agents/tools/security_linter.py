"""
Security Linter Tool
Checks code for common security vulnerabilities using Bandit.
"""

import tempfile
import os
from pydantic import BaseModel, Field
from typing import Dict, List
from bandit.core import manager as bandit_manager
from bandit.core import config as bandit_config


class SecurityIssue(BaseModel):
    """Individual security issue details."""
    severity: str = Field(description="Severity level: HIGH, MEDIUM, or LOW")
    confidence: str = Field(description="Confidence level: HIGH, MEDIUM, or LOW")
    issue_text: str = Field(description="Description of the security issue")
    test_id: str = Field(description="Bandit test ID (e.g., B101)")
    test_name: str = Field(description="Name of the security test")
    line_number: int = Field(description="Line number where issue was found")
    code: str = Field(description="The problematic code snippet")
    more_info: str = Field(description="URL with more information about the issue")


class SecurityReport(BaseModel):
    """Structured output for the security linter tool."""
    total_issues: int = Field(description="Total number of security issues found")
    high_severity: int = Field(description="Number of HIGH severity issues")
    medium_severity: int = Field(description="Number of MEDIUM severity issues")
    low_severity: int = Field(description="Number of LOW severity issues")
    issues: List[SecurityIssue] = Field(
        description="List of all security issues found",
        default_factory=list
    )
    metrics: Dict = Field(
        description="Additional metrics from the scan",
        default_factory=dict
    )


def security_linter(code: str, filename: str = "temp.py") -> Dict:
    """
    Analyzes code for security vulnerabilities using Bandit.
    
    Args:
        code: The source code string to analyze
        filename: Optional filename hint (helps Bandit apply correct tests)
        
    Returns:
        Dict containing SecurityReport or error information
    """
    try:
        # Create a temporary file to analyze
        # (Bandit requires file-based analysis)
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name

        try:
            # Initialize Bandit configuration
            b_config = bandit_config.BanditConfig()
            
            # Create Bandit manager
            b_mgr = bandit_manager.BanditManager(
                b_config,
                'file',
                profile=None,
                debug=False,
                verbose=False
            )
            
            # Discover and run all tests on the file
            b_mgr.discover_files([temp_path])
            b_mgr.run_tests()
            
            # Extract results
            results = b_mgr.results
            
            # Parse issues
            issues = []
            severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            
            for issue in results:
                severity = issue.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                issues.append(SecurityIssue(
                    severity=severity,
                    confidence=issue.confidence,
                    issue_text=issue.text,
                    test_id=issue.test_id,
                    test_name=issue.test,
                    line_number=issue.lineno,
                    code=issue.get_code(show_lineno=False).strip(),
                    more_info=issue.more_info or f"https://bandit.readthedocs.io/en/latest/plugins/{issue.test_id.lower()}.html"
                ))
            
            # Sort issues by severity
            severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            issues.sort(key=lambda x: severity_order[x.severity])
            
            # Get metrics
            metrics = b_mgr.metrics.data if hasattr(b_mgr, 'metrics') else {}
            
            return SecurityReport(
                total_issues=len(issues),
                high_severity=severity_counts.get('HIGH', 0),
                medium_severity=severity_counts.get('MEDIUM', 0),
                low_severity=severity_counts.get('LOW', 0),
                issues=issues,
                metrics=metrics
            ).model_dump()
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        return {
            "error": f"Security analysis failed: {e.__class__.__name__}",
            "details": str(e)
        }


# Example usage for testing
if __name__ == "__main__":
    sample_code = """
import pickle
import subprocess

def insecure_function(user_input):
    # This has multiple security issues
    data = pickle.loads(user_input)  # B301: Pickle usage
    subprocess.call(data, shell=True)  # B602: Shell injection risk
    password = "hardcoded_password123"  # B105: Hardcoded password
    return data
"""
    
    result = security_linter(sample_code)
    print(result)
