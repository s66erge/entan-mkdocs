import pytest
from libs.feedb import feedback_to_user, feed_text
from fasthtml.common import *

class TestFeedbackToUser:
    """Test feedback_to_user function."""

    def test_feedback_success_magic_link_sent(self):
        """Test success feedback for magic link sent."""
        result = feedback_to_user({'success': 'magic_link_sent'})
        assert 'sent' in to_xml(Html(result))
        assert 'email' in to_xml(Html(result))
        assert 'link' in to_xml(Html(result))

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
