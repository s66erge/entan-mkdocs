import pytest
from unittest.mock import Mock, patch
from fasthtml.common import NotFoundError
from libs.auth import (
    signin_form, login, create_link, send_magic_link_email,
    admin_required
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
        assert 'hx-post="/create_magic_link"' in form_html
        assert 'hx-target="#error"' in form_html


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


class TestCreateLink:
    """Test magic link creation."""

    def test_create_link_missing_email(self, mock_users):
        """Test create_link with missing email."""
        result = create_link("", mock_users)

        assert hasattr(result, 'tag')
        result_html = str(result)
        assert 'Email is required.' in result_html

    def test_create_link_user_not_found(self, mock_users):
        """Test create_link with non-existent user."""
        # Configure the mock to raise NotFoundError when accessed
        mock_users.__getitem__.side_effect = NotFoundError()

        result = create_link("nonexistent@example.com", mock_users)

        assert hasattr(result, 'tag')
        result_html = str(result)
        assert 'not registered' in result_html
        assert 'nonexistent@example.com' in result_html

    @patch('libs.auth.send_magic_link_email')
    @patch('libs.auth.os.environ.get')
    @patch('libs.auth.isa_dev_computer')
    def test_create_link_success_dev(self, mock_is_dev, mock_env_get, mock_send_email, mock_users):
        """Test create_link success on dev machine."""
        mock_is_dev.return_value = True
        mock_env_get.return_value = None

        result = create_link("test@example.com", mock_users)

        # Check that send_magic_link_email was called
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert call_args[0] == "test@example.com"
        assert "localhost:5001" in call_args[1]

        # Check result structure
        assert hasattr(result, 'tag') or isinstance(result, tuple)

    @patch('libs.auth.send_magic_link_email')
    @patch('libs.auth.os.environ.get')
    @patch('libs.auth.isa_dev_computer')
    def test_create_link_success_production(self, mock_is_dev, mock_env_get, mock_send_email, mock_users):
        """Test create_link success in production."""
        mock_is_dev.return_value = False
        mock_env_get.return_value = "myapp.railway.app"

        result = create_link("test@example.com", mock_users)

        # Check that send_magic_link_email was called
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert call_args[0] == "test@example.com"
        assert "https://myapp.railway.app" in call_args[1]


class TestSendMagicLinkEmail:
    """Test magic link email sending."""

    @patch('libs.auth.send_email')
    @patch('libs.auth.isa_dev_computer')
    def test_send_email_production(self, mock_is_dev, mock_send_email):
        """Test email sending in production."""
        mock_is_dev.return_value = False

        send_magic_link_email("test@example.com", "https://example.com/link")

        # Check that send_email was called with correct args
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert args[0] == "Sign in to The App"
        assert "https://example.com/link" in args[1]
        assert args[2] == ["test@example.com"]

    @patch('builtins.print')
    @patch('libs.auth.isa_dev_computer')
    def test_send_email_dev(self, mock_is_dev, mock_print):
        """Test email printing in development."""
        mock_is_dev.return_value = True

        send_magic_link_email("test@example.com", "https://example.com/link")

        # Check that print was called (not send_email)
        mock_print.assert_called_once()
        print_args = mock_print.call_args[0][0]
        assert "test@example.com" in print_args
        assert "Sign in to The App" in print_args


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
        assert hasattr(result, 'status_code')
        assert result.status_code == 307
        assert '/no_access_right' in str(result.headers)

    def test_admin_required_wrong_role(self, mock_session):
        """Test admin_required with non-admin role."""
        mock_session['role'] = 'user'

        @admin_required
        def test_handler(session):
            return "success"

        result = test_handler(mock_session)

        # Should redirect to no_access_right
        assert hasattr(result, 'status_code')
        assert result.status_code == 307
