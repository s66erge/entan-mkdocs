import pytest
import os
from fasthtml.common import *
from pathlib import Path
from datetime import date

from libs.utils import add_months_days, display_markdown, feedback_to_user

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

class TestFeedbackToUser:
    """Test feedback_to_user function."""

    def test_feedback_success_login_code_sent(self):
        """Test success feedback for login code sent."""
        result = feedback_to_user({'success': 'login_code_sent'})
        assert 'sent' in to_xml(Html(result))
        assert 'email' in to_xml(Html(result))
        assert 'code' in to_xml(Html(result))

    def test_feedback_error_missing_email(self):
        """Test error feedback for missing email."""
        result = feedback_to_user({'error': 'missing_email'})
        assert 'required' in to_xml(Html(result))
        assert 'Email' in to_xml(Html(result))

    def test_feedback_error_not_registered(self):
        """Test error feedback for not registered user."""
        result = feedback_to_user({'error': 'not_registered', 'email': 'test@example.com'})
        assert 'not registered' in to_xml(Html(result))
        assert 'test@example.com' in to_xml(Html(result))

    def test_feedback_unknown_type(self):
        """Test feedback for unknown feedback type."""
        result = feedback_to_user({'unknown': 'value'})
        assert '<p></p>' in to_xml(Html(result))

    def test_feedback_empty_dict(self):
        """Test feedback with empty dictionary."""
        result = feedback_to_user({})
        assert '<p></p>' in to_xml(Html(result))
