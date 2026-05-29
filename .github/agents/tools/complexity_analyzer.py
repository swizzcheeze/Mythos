"""
Complexity Analyzer Tool
Calculates quantitative code metrics using the radon library.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze


class FunctionComplexity(BaseModel):
    """Individual function complexity details."""
    name: str = Field(description="Function or method name")
    complexity: int = Field(description="Cyclomatic Complexity score")
    line_number: int = Field(description="Line number where function is defined")
    rank: str = Field(description="Complexity rank (A=simple, F=very complex)")


class CodeMetrics(BaseModel):
    """Structured output for the complexity analyzer tool."""
    cyclomatic_complexity_max: int = Field(
        description="The maximum Cyclomatic Complexity of the analyzed functions."
    )
    cyclomatic_complexity_avg: float = Field(
        description="Average Cyclomatic Complexity across all functions."
    )
    maintainability_index: float = Field(
        description="The Maintainability Index (MI) score, higher is better (0-100)."
    )
    loc: int = Field(description="Total Lines of Code (excluding blank and comments).")
    lloc: int = Field(description="Logical Lines of Code.")
    sloc: int = Field(description="Source Lines of Code (physical lines).")
    comments: int = Field(description="Number of comment lines.")
    blank: int = Field(description="Number of blank lines.")
    halstead_difficulty: Optional[float] = Field(
        description="Halstead difficulty metric (complexity from operator/operand usage)"
    )
    functions: List[FunctionComplexity] = Field(
        description="List of individual function complexities",
        default_factory=list
    )


def complexity_analyzer(code: str) -> Dict:
    """
    Analyzes code to determine its structural and maintainability metrics.
    
    Args:
        code: The source code string to analyze
        
    Returns:
        Dict containing CodeMetrics or error information
    """
    try:
        # 1. Cyclomatic Complexity (CC)
        cc_results = cc_visit(code)
        
        if cc_results:
            max_cc = max(f.complexity for f in cc_results)
            avg_cc = sum(f.complexity for f in cc_results) / len(cc_results)
            
            # Extract function details
            functions = [
                FunctionComplexity(
                    name=f.name,
                    complexity=f.complexity,
                    line_number=f.lineno,
                    rank=f.rank
                )
                for f in cc_results
            ]
        else:
            max_cc = 1
            avg_cc = 1.0
            functions = []

        # 2. Maintainability Index (MI)
        mi_score = mi_visit(code, multi=True)

        # 3. Raw Metrics (LOC, LLOC, SLOC, comments, blank)
        raw_metrics = analyze(code)
        
        # 4. Halstead Metrics (operator/operand complexity)
        try:
            halstead = h_visit(code)
            halstead_difficulty = halstead[0].difficulty if halstead else None
        except Exception:
            halstead_difficulty = None

        return CodeMetrics(
            cyclomatic_complexity_max=max_cc,
            cyclomatic_complexity_avg=round(avg_cc, 2),
            maintainability_index=round(mi_score, 2),
            loc=raw_metrics.loc,
            lloc=raw_metrics.lloc,
            sloc=raw_metrics.sloc,
            comments=raw_metrics.comments,
            blank=raw_metrics.blank,
            halstead_difficulty=round(halstead_difficulty, 2) if halstead_difficulty else None,
            functions=functions
        ).model_dump()

    except Exception as e:
        return {
            "error": f"Complexity analysis failed: {e.__class__.__name__}",
            "details": str(e)
        }


# Example usage for testing
if __name__ == "__main__":
    sample_code = """
def add(a, b):
    return a + b

def complex_function(x, y, z):
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
    
    result = complexity_analyzer(sample_code)
    print(result)
