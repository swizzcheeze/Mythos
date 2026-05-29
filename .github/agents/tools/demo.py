#!/usr/bin/env python3
"""
Code Review Agent Demo
Demonstrates the complete workflow of the code reviewer agent using all three tools.
"""

import sys
import json
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from complexity_analyzer import complexity_analyzer
from security_linter import security_linter
from codespace_file_reader import codespace_file_reader


def generate_review_report(filepath: str) -> dict:
    """
    Simulates the agent's complete code review workflow.
    
    Args:
        filepath: Path to the file to review
        
    Returns:
        Comprehensive review report
    """
    print(f"🔍 Starting code review for: {filepath}\n")
    
    # Step 1: Read the file
    print("📂 Step 1: Reading file...")
    file_data = codespace_file_reader(filepath)
    
    if 'error' in file_data:
        return {
            "status": "error",
            "message": f"Failed to read file: {file_data['error']}",
            "details": file_data.get('details', '')
        }
    
    print(f"   ✓ Read {file_data['lines']} lines ({file_data['size_bytes']} bytes)")
    print(f"   ✓ Language: {file_data['language']}")
    
    code = file_data['content']
    
    # Step 2: Analyze complexity
    print("\n📊 Step 2: Analyzing code complexity...")
    complexity_data = complexity_analyzer(code)
    
    if 'error' in complexity_data:
        print(f"   ⚠ Complexity analysis failed: {complexity_data['error']}")
    else:
        print(f"   ✓ Max Cyclomatic Complexity: {complexity_data['cyclomatic_complexity_max']}")
        print(f"   ✓ Maintainability Index: {complexity_data['maintainability_index']:.1f}/100")
        print(f"   ✓ Logical Lines of Code: {complexity_data['lloc']}")
    
    # Step 3: Security analysis
    print("\n🔒 Step 3: Running security scan...")
    security_data = security_linter(code)
    
    if 'error' in security_data:
        print(f"   ⚠ Security scan failed: {security_data['error']}")
    else:
        print(f"   ✓ Total issues found: {security_data['total_issues']}")
        print(f"   ✓ HIGH severity: {security_data['high_severity']}")
        print(f"   ✓ MEDIUM severity: {security_data['medium_severity']}")
        print(f"   ✓ LOW severity: {security_data['low_severity']}")
    
    # Step 4: Generate summary report
    print("\n" + "="*80)
    print("📋 CODE REVIEW SUMMARY REPORT")
    print("="*80)
    
    # Summary Scorecard
    overall_score = calculate_overall_score(complexity_data, security_data)
    print(f"\n🎯 Overall Quality Score: {overall_score}/100")
    print(f"   File: {filepath}")
    print(f"   Lines: {file_data['lines']}")
    print(f"   Language: {file_data['language']}")
    
    # Critical Issues
    print("\n🚨 CRITICAL ISSUES")
    if 'error' not in security_data and security_data['high_severity'] > 0:
        for issue in security_data['issues']:
            if issue['severity'] == 'HIGH':
                print(f"   • Line {issue['line_number']}: {issue['issue_text']}")
                print(f"     [{issue['test_id']}] More info: {issue['more_info']}")
    else:
        print("   ✓ No critical security issues detected")
    
    # Major Issues
    print("\n⚠️  MAJOR ISSUES")
    major_issues = []
    
    # High complexity
    if 'error' not in complexity_data:
        if complexity_data['cyclomatic_complexity_max'] > 10:
            major_issues.append(
                f"High cyclomatic complexity detected (max: {complexity_data['cyclomatic_complexity_max']}). "
                f"Consider refactoring complex functions."
            )
        
        # Low maintainability
        if complexity_data['maintainability_index'] < 50:
            major_issues.append(
                f"Low maintainability index ({complexity_data['maintainability_index']:.1f}/100). "
                f"Code may be difficult to maintain."
            )
    
    # Medium security issues
    if 'error' not in security_data and security_data['medium_severity'] > 0:
        for issue in security_data['issues']:
            if issue['severity'] == 'MEDIUM':
                major_issues.append(
                    f"Line {issue['line_number']}: {issue['issue_text']} [{issue['test_id']}]"
                )
    
    if major_issues:
        for issue in major_issues:
            print(f"   • {issue}")
    else:
        print("   ✓ No major issues detected")
    
    # Minor Issues
    print("\n💡 MINOR ISSUES & SUGGESTIONS")
    if 'error' not in security_data and security_data['low_severity'] > 0:
        for issue in security_data['issues']:
            if issue['severity'] == 'LOW':
                print(f"   • Line {issue['line_number']}: {issue['issue_text']}")
    else:
        print("   ✓ No minor issues detected")
    
    # Recommendations
    print("\n✅ RECOMMENDATIONS")
    recommendations = generate_recommendations(complexity_data, security_data)
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   ✓ Code meets all quality standards!")
    
    print("\n" + "="*80)
    
    return {
        "status": "success",
        "overall_score": overall_score,
        "file_info": file_data,
        "complexity": complexity_data,
        "security": security_data
    }


def calculate_overall_score(complexity_data: dict, security_data: dict) -> int:
    """Calculate an overall quality score from 0-100."""
    score = 100
    
    # Deduct for complexity issues
    if 'error' not in complexity_data:
        if complexity_data['maintainability_index'] < 100:
            score -= (100 - complexity_data['maintainability_index']) * 0.3
        
        if complexity_data['cyclomatic_complexity_max'] > 10:
            score -= (complexity_data['cyclomatic_complexity_max'] - 10) * 2
    
    # Deduct for security issues
    if 'error' not in security_data:
        score -= security_data['high_severity'] * 20
        score -= security_data['medium_severity'] * 10
        score -= security_data['low_severity'] * 2
    
    return max(0, min(100, int(score)))


def generate_recommendations(complexity_data: dict, security_data: dict) -> list:
    """Generate actionable recommendations."""
    recommendations = []
    
    if 'error' not in complexity_data:
        if complexity_data['cyclomatic_complexity_max'] > 15:
            recommendations.append(
                "Refactor functions with high complexity (>15) by extracting logical blocks into separate functions"
            )
        
        if complexity_data['maintainability_index'] < 65:
            recommendations.append(
                "Improve code maintainability by adding docstrings, reducing nesting, and simplifying logic"
            )
        
        # Check comment ratio
        if complexity_data['lloc'] > 50:
            comment_ratio = complexity_data['comments'] / complexity_data['lloc']
            if comment_ratio < 0.1:
                recommendations.append(
                    "Add more inline comments and docstrings (current ratio is low)"
                )
    
    if 'error' not in security_data:
        if security_data['high_severity'] > 0:
            recommendations.append(
                "Address all HIGH severity security issues immediately before deployment"
            )
        
        if security_data['medium_severity'] > 0:
            recommendations.append(
                "Review and fix MEDIUM severity security issues"
            )
    
    return recommendations


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python demo.py <filepath> [filepath2] [filepath3] ...")
        print("Example: python demo.py src/main.py")
        print("Example: python demo.py src/**/*.py")
        sys.exit(1)
    
    # Use files from command line
    test_files = sys.argv[1:]
    
    for filepath in test_files:
        result = generate_review_report(filepath)
        print("\n")
        
        if result['status'] == 'error':
            print(f"❌ Review failed: {result['message']}")
        
        # Pause between multiple files
        if len(test_files) > 1:
            print("\n" + "="*80 + "\n")
