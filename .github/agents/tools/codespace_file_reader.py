"""
Codespace File Reader Tool
Safely reads files from the workspace with sandboxing constraints.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Optional


class FileContent(BaseModel):
    """Structured output for the file reader tool."""
    filepath: str = Field(description="The absolute path of the file that was read")
    content: str = Field(description="The content of the file")
    lines: int = Field(description="Number of lines in the file")
    size_bytes: int = Field(description="Size of the file in bytes")
    encoding: str = Field(description="Character encoding used to read the file")
    language: Optional[str] = Field(
        description="Detected programming language based on file extension",
        default=None
    )


def detect_language(filepath: str) -> Optional[str]:
    """
    Detect the programming language based on file extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Language name or None
    """
    ext_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JSX',
        '.tsx': 'TSX',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.md': 'Markdown',
    }
    
    ext = Path(filepath).suffix.lower()
    return ext_map.get(ext)


def codespace_file_reader(
    filepath: str,
    workspace_root: str = None
) -> Dict:
    """
    Safely reads a file from the workspace with sandboxing.
    
    Args:
        filepath: Relative or absolute path to the file within the workspace
        workspace_root: Root directory of the workspace (for sandboxing). If None, auto-detects.
        
    Returns:
        Dict containing FileContent or error information
    """
    try:
        # Auto-detect workspace root if not provided
        if workspace_root is None:
            workspace_root = os.getcwd()
        
        # Normalize the workspace root
        workspace_path = Path(workspace_root).resolve()
        
        # Convert filepath to absolute path
        if os.path.isabs(filepath):
            file_path = Path(filepath).resolve()
        else:
            # Treat as relative to workspace root
            file_path = (workspace_path / filepath).resolve()
        
        # Security check: Ensure the file is within the workspace
        try:
            file_path.relative_to(workspace_path)
        except ValueError:
            return {
                "error": "SecurityError: Access denied",
                "details": f"File '{filepath}' is outside the workspace boundary. "
                          f"Only files within '{workspace_root}' can be accessed."
            }
        
        # Check if file exists
        if not file_path.exists():
            return {
                "error": "FileNotFoundError",
                "details": f"File '{filepath}' does not exist in the workspace."
            }
        
        # Check if it's a file (not a directory)
        if not file_path.is_file():
            return {
                "error": "IsADirectoryError",
                "details": f"'{filepath}' is a directory, not a file."
            }
        
        # Get file size
        size_bytes = file_path.stat().st_size
        
        # Limit file size to prevent memory issues (10MB max)
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        if size_bytes > MAX_SIZE:
            return {
                "error": "FileTooLargeError",
                "details": f"File '{filepath}' is {size_bytes} bytes, "
                          f"which exceeds the maximum allowed size of {MAX_SIZE} bytes."
            }
        
        # Try to read the file with UTF-8 encoding
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                used_encoding = encoding
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if content is None:
            return {
                "error": "EncodingError",
                "details": f"Unable to read '{filepath}' with supported encodings: {encodings}"
            }
        
        # Count lines
        line_count = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
        
        # Detect language
        language = detect_language(str(file_path))
        
        return FileContent(
            filepath=str(file_path),
            content=content,
            lines=line_count,
            size_bytes=size_bytes,
            encoding=used_encoding,
            language=language
        ).model_dump()

    except Exception as e:
        return {
            "error": f"File read failed: {e.__class__.__name__}",
            "details": str(e)
        }


# Example usage for testing
if __name__ == "__main__":
    # Test reading a Python file from the workspace
    import sys
    if len(sys.argv) > 1:
        result = codespace_file_reader(sys.argv[1])
        print(result)
    else:
        print("Usage: python codespace_file_reader.py <filepath>")
        print("Example: python codespace_file_reader.py README.md")
