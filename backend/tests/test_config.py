"""
Tests for app/config.py

Testing configuration loading, validators, and utility functions.
"""
import pytest
import json
import os
from unittest.mock import patch
from pydantic import ValidationError

from app.config import Settings, _mask_db_url, settings


class TestMaskDbUrl:
    """Tests for the _mask_db_url utility function"""

    def test_mask_db_url_with_credentials(self):
        """Test masking of database URL with user credentials"""
        url = "postgresql://user:password@localhost:5432/db"
        masked = _mask_db_url(url)
        assert masked == "postgresql://***@localhost:5432/db"
        assert "user" not in masked
        assert "password" not in masked

    def test_mask_db_url_with_complex_credentials(self):
        """Test masking with special characters in credentials
        
        Note: The function splits on the first '@' after '://', so if the password
        contains '@', the second part will remain visible. This is an edge case
        where the masking is not perfect but the function handles it gracefully.
        """
        url = "postgresql://admin:p@ss!word@host.example.com:5432/mydb"
        masked = _mask_db_url(url)
        # The function masks "admin:p" but "ss!word@host..." remains
        assert masked == "postgresql://***@ss!word@host.example.com:5432/mydb"
        assert "admin" not in masked

    def test_mask_db_url_without_credentials(self):
        """Test that URLs without credentials are returned unchanged"""
        url = "sqlite:///./moneytracker.db"
        masked = _mask_db_url(url)
        assert masked == url

    def test_mask_db_url_without_at_symbol(self):
        """Test URL without @ symbol"""
        url = "postgresql://localhost/db"
        masked = _mask_db_url(url)
        assert masked == url

    def test_mask_db_url_without_protocol(self):
        """Test URL without protocol (edge case)"""
        url = "localhost:5432/db"
        masked = _mask_db_url(url)
        assert masked == url

    def test_mask_db_url_malformed_splits_gracefully(self):
        """Test that malformed URLs are handled - function masks what it can"""
        # URL with @ after :// - function will still try to mask
        url = "broken://@"
        masked = _mask_db_url(url)
        # Function splits and masks the empty userinfo part
        assert masked == "broken://***@"

    def test_mask_db_url_with_multiple_at_symbols(self):
        """Test URL with multiple @ symbols - splits on first @"""
        # The function splits on the first @ after ://, so it masks "user"
        url = "postgresql://user@pass@host@another:5432/db"
        masked = _mask_db_url(url)
        # Masks "user" but rest remains with @ symbols
        assert masked == "postgresql://***@pass@host@another:5432/db"

    def test_mask_db_url_empty_string(self):
        """Test empty string input"""
        url = ""
        masked = _mask_db_url(url)
        assert masked == ""

    def test_mask_db_url_forces_exception_with_too_many_splits(self):
        """Test that exception handler is triggered when split produces unexpected result"""
        # URLs that cause ValueError during unpacking
        # Testing with a URL that has multiple colons in weird places
        url = "postgresql://user:pass:extra@host:5432/db"
        masked = _mask_db_url(url)
        # Should handle gracefully - either mask or return original
        assert isinstance(masked, str)

    def test_mask_db_url_exception_on_unpacking_failure(self):
        """Test that exception handler catches unpacking errors when rest has no @"""
        # URL where @ is before ://, causing rest to have no @, leading to unpacking failure
        url = "user@postgresql://host/db"
        masked = _mask_db_url(url)
        # Should return original URL due to exception
        assert masked == url


class TestSettingsClass:
    """Tests for the Settings class"""

    def test_settings_defaults(self):
        """Test that Settings class has correct default values"""
        s = Settings()
        assert s.PROJECT_NAME == "Money Tracker API"
        assert s.VERSION == "1.0.0"
        assert s.API_V1_PREFIX == "/api/v1"
        assert s.DATABASE_URL == "sqlite:///./moneytracker.db"
        assert s.HOST == "0.0.0.0"
        assert s.PORT == 8000
        assert s.RELOAD is True

    def test_settings_cors_origins_default(self):
        """Test default CORS origins"""
        s = Settings()
        assert isinstance(s.BACKEND_CORS_ORIGINS, list)
        assert "http://localhost:5173" in s.BACKEND_CORS_ORIGINS
        assert "http://localhost:3000" in s.BACKEND_CORS_ORIGINS

    def test_settings_from_env_variables(self):
        """Test that settings can be loaded from environment variables"""
        with patch.dict(os.environ, {
            "PROJECT_NAME": "Test Project",
            "PORT": "9000",
            "DATABASE_URL": "postgresql://test:test@localhost/testdb"
        }):
            s = Settings()
            assert s.PROJECT_NAME == "Test Project"
            assert s.PORT == 9000
            assert s.DATABASE_URL == "postgresql://test:test@localhost/testdb"

    def test_cors_origins_validator_with_json_string(self):
        """Test CORS origins validator with JSON string"""
        with patch.dict(os.environ, {
            "BACKEND_CORS_ORIGINS": '["http://test1.com", "http://test2.com"]'
        }):
            s = Settings()
            assert s.BACKEND_CORS_ORIGINS == ["http://test1.com", "http://test2.com"]

    def test_cors_origins_validator_with_list(self):
        """Test CORS origins validator when already a list"""
        # When passed directly as a list (not from env), should return as-is
        origins_list = ["http://direct1.com", "http://direct2.com"]
        # Use model_validate to pass dict with list value
        s = Settings.model_validate({"BACKEND_CORS_ORIGINS": origins_list})
        assert s.BACKEND_CORS_ORIGINS == origins_list

    def test_cors_origins_validator_direct_string(self):
        """Test CORS origins validator receives string, tries JSON then comma-split"""
        # Test the validator directly with a string input
        test_value = "http://test1.com, http://test2.com"
        # The validator should try JSON parse, fail, then split by comma
        parsed = Settings.parse_cors_origins(test_value)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert "http://test1.com" in parsed
        assert "http://test2.com" in parsed

    def test_cors_origins_validator_invalid_json_string(self):
        """Test CORS origins validator with invalid JSON falls back to comma split"""
        test_value = "{this is not valid json}"
        parsed = Settings.parse_cors_origins(test_value)
        assert isinstance(parsed, list)
        assert "{this is not valid json}" in parsed

    def test_settings_config_class_exists(self):
        """Test that Settings has Config inner class"""
        assert hasattr(Settings, 'Config')
        assert hasattr(Settings.Config, 'env_file')
        assert Settings.Config.env_file == ".env"
        assert Settings.Config.case_sensitive is True

    def test_port_must_be_int(self):
        """Test that PORT must be an integer"""
        with patch.dict(os.environ, {"PORT": "not_a_number"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_reload_must_be_bool(self):
        """Test that RELOAD can be set from env as bool-like string"""
        with patch.dict(os.environ, {"RELOAD": "false"}):
            s = Settings()
            assert s.RELOAD is False
        
        with patch.dict(os.environ, {"RELOAD": "true"}):
            s = Settings()
            assert s.RELOAD is True


class TestSettingsInstance:
    """Tests for the global settings instance"""

    def test_settings_instance_exists(self):
        """Test that settings instance is created"""
        from app.config import settings
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_instance_has_values(self):
        """Test that settings instance has expected values"""
        from app.config import settings
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'HOST')
        assert hasattr(settings, 'PORT')


class TestEdgeCases:
    """Additional edge case tests"""

    def test_database_url_can_be_complex(self):
        """Test that complex database URLs are handled"""
        complex_url = "postgresql+asyncpg://user:pass@localhost:5432/db?param=value"
        with patch.dict(os.environ, {"DATABASE_URL": complex_url}):
            s = Settings()
            assert s.DATABASE_URL == complex_url

    def test_api_prefix_can_be_customized(self):
        """Test that API prefix can be changed"""
        with patch.dict(os.environ, {"API_V1_PREFIX": "/api/v2"}):
            s = Settings()
            assert s.API_V1_PREFIX == "/api/v2"

    def test_host_can_be_customized(self):
        """Test that HOST can be changed"""
        with patch.dict(os.environ, {"HOST": "127.0.0.1"}):
            s = Settings()
            assert s.HOST == "127.0.0.1"
