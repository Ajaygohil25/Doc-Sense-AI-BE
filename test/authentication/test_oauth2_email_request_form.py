import pytest
from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm
from app.authentication.oauth2 import OAuth2EmailRequestForm


class TestOAuth2EmailRequestForm:
    """Test cases for OAuth2EmailRequestForm class."""
    
    def test_valid_email_and_password_initialization(self):
        """Test initialization with valid email and password."""
        email = "test@example.com"
        password = "test_password"
        
        form = OAuth2EmailRequestForm.__new__(OAuth2EmailRequestForm)
        form.__init__(
            email=email,
            password=password
        )
        
        assert form.email == email
        assert form.username == email  # inherited from parent
        assert form.password == password
        assert form.scope == ""  # default value
        assert form.client_id is None  # default value
        assert form.client_secret is None  # default value
    
    def test_all_optional_parameters_provided(self):
        """Test initialization with all optional parameters."""
        email = "user@domain.com"
        password = "secure_password"
        scope = "read write"
        client_id = "test_client_id"
        client_secret = "test_client_secret"
        
        form = OAuth2EmailRequestForm.__new__(OAuth2EmailRequestForm)
        form.__init__(
            email=email,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret
        )
        
        assert form.email == email
        assert form.username == email
        assert form.password == password
        assert form.scope == scope
        assert form.client_id == client_id
        assert form.client_secret == client_secret
    
    def test_empty_scope_defaults_correctly(self):
        """Test that empty scope parameter defaults to empty string."""
        email = "test@example.com"
        password = "test_password"
        
        form = OAuth2EmailRequestForm.__new__(OAuth2EmailRequestForm)
        form.__init__(
            email=email,
            password=password,
            scope=""
        )
        
        assert form.scope == ""
        assert form.email == email
        assert form.password == password
    
    def test_none_client_id_and_client_secret(self):
        """Test that None client_id and client_secret are handled correctly."""
        email = "test@example.com"
        password = "test_password"
        
        form = OAuth2EmailRequestForm.__new__(OAuth2EmailRequestForm)
        form.__init__(
            email=email,
            password=password,
            client_id=None,
            client_secret=None
        )
        
        assert form.client_id is None
        assert form.client_secret is None
        assert form.email == email
        assert form.password == password
    
    def test_email_stored_in_both_attributes(self):
        """Test that email is stored in both email and username attributes."""
        email = "user@example.com"
        password = "password123"
        
        form = OAuth2EmailRequestForm.__new__(OAuth2EmailRequestForm)
        form.__init__(
            email=email,
            password=password
        )
        
        # Email should be stored in both places
        assert form.email == email
        assert form.username == email
        assert form.email == form.username
    
    def test_inheritance_from_oauth2_password_request_form_works(self):
        """Test that the class properly inherits from OAuth2PasswordRequestForm."""
        email = "test@example.com"
        password = "test_password"
        scope = "read"
        client_id = "client123"
        client_secret = "secret456"
        
        form = OAuth2EmailRequestForm.__new__(OAuth2EmailRequestForm)
        form.__init__(
            email=email,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Check inheritance
        assert isinstance(form, OAuth2PasswordRequestForm)
        assert isinstance(form, OAuth2EmailRequestForm)
        
        # Check that all parent class attributes are accessible
        assert hasattr(form, 'username')
        assert hasattr(form, 'password')
        assert hasattr(form, 'scope')
        assert hasattr(form, 'client_id')
        assert hasattr(form, 'client_secret')
        
        # Check that the parent class username is set to email
        assert form.username == email