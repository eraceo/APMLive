import os
import sys
import logging
import pytest
from unittest.mock import patch, MagicMock
from src.utils.logger import setup_logger


@pytest.fixture
def clean_logger():
    """Remove all handlers from the logger before and after each test."""
    logger = logging.getLogger("APMLive")
    # Clear existing handlers
    logger.handlers = []
    yield
    logger.handlers = []


def test_setup_logger_basic(clean_logger):
    """Test basic logger setup."""
    logger = setup_logger("APMLive")
    assert logger.name == "APMLive"
    assert logger.level == logging.DEBUG
    # Should have at least a console handler
    assert len(logger.handlers) >= 1


def test_setup_logger_existing_handlers(clean_logger):
    """Test that setup_logger returns existing logger if it already has handlers."""
    logger = logging.getLogger("APMLive")
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    logger_new = setup_logger("APMLive")
    assert logger_new is logger
    assert len(logger_new.handlers) == 1
    assert logger_new.handlers[0] is handler


@patch("sys.platform", "win32")
@patch("os.getenv")
@patch("src.utils.logger.Path")
@patch("src.utils.logger.RotatingFileHandler")
def test_setup_logger_windows_localaapdata(
    mock_rfh, mock_path, mock_getenv, clean_logger
):
    """Test logger setup on Windows with LOCALAPPDATA."""
    mock_getenv.return_value = r"C:\Users\Test\AppData\Local"

    # Mock Path behavior
    mock_path_obj = MagicMock()
    mock_path.return_value = mock_path_obj
    mock_path_obj.__truediv__.return_value = mock_path_obj  # Support / operator

    setup_logger("APMLive")

    # Check if Path was instantiated
    assert mock_path.called

    # Check if RotatingFileHandler was instantiated
    assert mock_rfh.called


@patch("sys.platform", "win32")
@patch("os.getenv")
@patch("src.utils.logger.Path")
def test_setup_logger_windows_no_localaapdata(mock_path, mock_getenv, clean_logger):
    """Test logger setup on Windows without LOCALAPPDATA."""
    mock_getenv.return_value = None

    # Mock Path.cwd()
    mock_cwd = MagicMock()
    mock_path.cwd.return_value = mock_cwd
    mock_cwd.__truediv__.return_value = mock_cwd

    setup_logger("APMLive")

    # Should use cwd
    assert mock_path.cwd.called


@patch("sys.platform", "linux")
@patch("src.utils.logger.Path")
def test_setup_logger_linux(mock_path, clean_logger):
    """Test logger setup on Linux (non-win32)."""
    # Mock Path.home()
    mock_home = MagicMock()
    mock_path.home.return_value = mock_home
    mock_home.__truediv__.return_value = mock_home

    setup_logger("APMLive")

    # Should use home
    assert mock_path.home.called


@patch("src.utils.logger.Path")
def test_setup_logger_permission_error(mock_path, clean_logger, capsys):
    """Test handling of permission error when creating log directory."""
    mock_path_obj = MagicMock()
    mock_path.return_value = mock_path_obj
    mock_path_obj.__truediv__.return_value = mock_path_obj

    # Raise OSError when mkdir is called
    mock_path_obj.mkdir.side_effect = PermissionError("Access denied")

    logger = setup_logger("APMLive")

    captured = capsys.readouterr()
    assert "Failed to create log file" in captured.out


def test_log_rotation_configuration():
    """
    Verify that log rotation is configured correctly to prevent infinite growth.
    Requirement: maxBytes should be reasonable (e.g. 1MB) and backupCount limited (e.g. 5).
    """
    with patch("src.utils.logger.RotatingFileHandler") as MockRFH:
        # Reset logger handlers to force recreation
        logger = logging.getLogger("APMLive")
        logger.handlers = []

        setup_logger("APMLive")

        # Verify RotatingFileHandler was initialized with correct parameters
        assert MockRFH.called
        call_args = MockRFH.call_args
        _, kwargs = call_args

        # Check maxBytes (1MB = 1048576 bytes)
        assert (
            kwargs.get("maxBytes") == 1024 * 1024
        ), "Log rotation maxBytes should be 1MB"

        # Check backupCount (5 files)
        assert kwargs.get("backupCount") == 5, "Log rotation backupCount should be 5"

        # Check encoding
        assert kwargs.get("encoding") == "utf-8", "Log encoding should be utf-8"
