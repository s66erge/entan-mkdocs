import pytest
import os
from pathlib import Path
from datetime import date

from libs.utils import add_months_days, display_markdown

def test_add_months_days_basic():
    """Test adding months and days to a date."""
    result = add_months_days("2025-02-25", 6, 15)
    assert result == "2025-09-09"

def test_add_months_days_zero():
    """Test with zero months and days."""
    result = add_months_days("2025-02-25", 0, 0)
    assert result == "2025-02-25"

def test_add_months_days_end_of_month():
    """Test end-of-month preservation (Feb 29 -> Feb 28 in non-leap year)."""
    result = add_months_days("2024-02-29", 12, 0)  # 2024 is leap year
    assert result == "2025-02-28"  # 2025 is not leap year

def test_display_markdown_basic(tmp_path):
    """Test displaying a markdown file."""
    # Create a temporary md-text directory
    md_dir = tmp_path / "md-text"
    md_dir.mkdir()
    
    # Create a test markdown file
    test_file = md_dir / "test.md"
    test_file.write_text("# Hello\n\nThis is a **test**.")
    
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        result = display_markdown("test")
        assert "<h1>Hello</h1>" in str(result)
        assert "<strong>test</strong>" in str(result)
    finally:
        os.chdir(original_cwd)

def test_display_markdown_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        display_markdown("nonexistent_file")


