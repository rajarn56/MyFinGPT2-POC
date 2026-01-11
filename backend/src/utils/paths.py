"""Path utilities for resolving project-relative paths"""

from pathlib import Path
import os


def get_project_root() -> Path:
    """
    Get the project root directory (MyFinGPT2-POC/)
    
    In local development: backend/src/utils/paths.py -> project root is 3 levels up
    In Docker: /app/src/utils/paths.py, but data is mounted at /app/data
    
    Returns:
        Path to project root (or /app in Docker)
    """
    current_file = Path(__file__).resolve()
    
    # Check if we're in Docker (data mounted at /app/data)
    if current_file.parts[0] == "/" and len(current_file.parts) > 1 and current_file.parts[1] == "app":
        # In Docker: /app/src/utils/paths.py
        # Data is mounted at /app/data, so use /app as base
        return Path("/app")
    
    # Local development: backend/src/utils/paths.py
    # Project root is 3 levels up from this file
    project_root = current_file.parent.parent.parent.parent
    return project_root


def get_data_path(subpath: str = "") -> Path:
    """
    Get path to data directory
    
    In local: project_root/data/
    In Docker: /app/data/ (mounted from project root)
    
    Args:
        subpath: Subpath within data directory (e.g., "chroma", "sessions")
    
    Returns:
        Path to data directory or subdirectory
    """
    project_root = get_project_root()
    
    # In Docker, data is mounted at /app/data
    # In local, data is at project_root/data
    if project_root == Path("/app"):
        # Docker: data is mounted at /app/data
        data_path = Path("/app/data")
    else:
        # Local: data is at project_root/data
        data_path = project_root / "data"
    
    if subpath:
        return data_path / subpath
    return data_path


def get_logs_path() -> Path:
    """
    Get path to logs directory
    
    In local: project_root/logs/
    In Docker: /app/logs/ (mounted from project root)
    
    Returns:
        Path to logs directory
    """
    project_root = get_project_root()
    
    # In Docker, logs are mounted at /app/logs
    # In local, logs are at project_root/logs
    if project_root == Path("/app"):
        return Path("/app/logs")
    else:
        return project_root / "logs"
