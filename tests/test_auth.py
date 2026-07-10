import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from fasthtml.common import to_xml
from libs.messages import feed_text
from libs.auth import (
    signin_form, login, create_code, send_login_code_email,
    verify_code, admin_required
)


@pytest.fixture
def mock_users():
    """Create a mock users table."""
    users = Mock()

    # Mock existing user
    mock_user = Mock()
    mock_user.email = "test@example.com"
    mock_user.role_name = "user"

    # Configure __getitem__ behavior
    users.__getitem__ = Mock(return_value=mock_user)

    return users


@pytest.fixture
def mock_session():
    """Create a mock session."""
    return {}


class TestSigninForm:
    """Test signin form generation."""

    def test_signin_form_structure(self):
        """Test that signin_form returns a properly structured Form."""
        form = signin_form()

        # Check it's a Form element
        assert hasattr(form, 'tag')
        assert form.tag == 'form'

        # Check it has email input
        form_html = str(form)
        assert 'type="email"' in form_html
        assert 'placeholder="foo@bar.com"' in form_html

        # Check it has submit button
        assert 'type="submit"' in form_html
        assert 'Sign In with Email' in form_html

        # Check HTMX attributes
        assert 'hx-post="/create_code"' in form_html
        assert 'hx-target="#signin-error"' in form_html


class TestLogin:
    """Test login page generation."""

    def test_login_page_structure(self):
        """Test that login() returns properly structured Main element."""
        main = login()

        # Check it's a Main element
        assert hasattr(main, 'tag')
        assert main.tag == 'main'

        # Check content
        main_html = str(main)
        assert 'Sign In' in main_html
        assert 'Enter your email to sign in' in main_html
        assert 'container' in main_html


class TestCreateCode:
    """Test magic link creation."""

    def test_create_code_missing_email(self, mock_users):
        """Test create_code with missing email."""
        result = create_code("", mock_users)

        assert hasattr(result, 'tag')
        result_html = str(result)
        assert 'Email is required.' in result_html

    def test_create_code_user_not_found(self, mock_users):
        """Test create_code with non-existent user."""
        # Configure the mock to raise IndexError when accessed
        mock_users.side_effect = IndexError()

        result = create_code("nonexistent@example.com", mock_users)

        assert hasattr(result, 'tag')
        result_html = str(result)
        assert 'not registered' in result_html
        assert 'nonexistent@example.com' in result_html

    @patch('libs.auth.send_login_code_email')
    @patch('libs.auth.datetime')
    @patch('libs.auth.secrets')
    def test_create_code_success(self, mock_secrets, mock_datetime, mock_send_email, mock_users):
        """Test create_code success: generates a code and emails it to the user."""
        mock_secrets.choice.return_value = '4'
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_users.return_value = [Mock(email="test@example.com", role_name="user")]

        result = create_code("test@example.com", mock_users)

        # Check that send_login_code_email was called with the generated code
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert call_args[0] == "test@example.com"
        assert call_args[1] == "444444"  # 6-digit code from mock

        # Check result structure (create_code returns a tuple of FT partials on success)
        assert hasattr(result, 'tag') or isinstance(result, tuple)


class TestSendLoginCodeEmail:
    """Test magic link email sending."""

    @patch('libs.utils.send_email')
    def test_send_login_code_email(self, mock_send_email):
        """send_login_code_email delegates to utils.send_email with subject, text and recipient."""
        send_login_code_email("test@example.com", "123456")

        # Check that send_email was called with correct args
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert "Your sign-in code for The App" in args[0]
        assert "123456" in args[1]
        assert args[2] == ["test@example.com"]


class TestVerifyCode:
    """Test code verification."""

    @patch('libs.auth.datetime')
    def test_verify_code_invalid_code(self, mock_datetime, mock_users):
        """Test verify_code with invalid code."""
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        # Configure the mock to raise IndexError when accessed
        mock_users.side_effect = IndexError()

        result = verify_code({}, "invalid_code", "UTC", mock_users)

        # Should return the "invalid or expired code" error feedback. Derive the
        # expected copy from feed_text so the assertion tracks the source of truth
        # rather than hard-coding the (currently typoed) sentence.
        expected = feed_text({"error": "invalid_or_expired_code"})["mess"]
        assert expected in to_xml(result)

    @patch('libs.auth.datetime')
    def test_verify_code_valid_code(self, mock_datetime, mock_users):
        """Test verify_code with valid code."""
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_user = Mock(email="test@example.com", role_name="user")
        mock_users.return_value = [mock_user]
        
        session = {}
        result = verify_code(session, "valid_code", "UTC", mock_users)

        # Check session was updated
        assert session['auth'] == "test@example.com"
        assert session['role'] == "user"

        # Check result is a redirect to the dashboard
        assert type(result).__name__ == "Redirect"
        assert result.loc == "/dashboard"


class TestAdminRequired:
    """Test admin_required decorator."""

    def test_admin_required_success(self, mock_session):
        """Test admin_required with admin user."""
        mock_session['role'] = 'admin'

        @admin_required
        def test_handler(session):
            return "success"

        result = test_handler(mock_session)
        assert result == "success"

    def test_admin_required_no_role(self, mock_session):
        """Test admin_required with no role set."""
        # No role in session
        mock_session['role'] = ''

        @admin_required
        def test_handler(session):
            return "success"

        result = test_handler(mock_session)

        # Should redirect to no_access_right
        assert type(result).__name__ == "Redirect"
        assert result.loc == "/no_access_right"

    def test_admin_required_wrong_role(self, mock_session):
        """Test admin_required with non-admin role."""
        mock_session['role'] = 'user'

        @admin_required
        def test_handler(session):
            return "success"

        result = test_handler(mock_session)

        # Should redirect to no_access_right
        assert type(result).__name__ == "Redirect"
        assert result.loc == "/no_access_right"