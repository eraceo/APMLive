
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
def test_setup_logger_windows_localaapdata(mock_rfh, mock_path, mock_getenv, clean_logger):
    """Test logger setup on Windows with LOCALAPPDATA."""
    mock_getenv.return_value = r"C:\Users\Test\AppData\Local"
    
    # Mock Path behavior
    mock_path_obj = MagicMock()
    mock_path.return_value = mock_path_obj
    mock_path_obj.__truediv__.return_value = mock_path_obj # Support / operator
    
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
    
    # Should still return logger, but maybe only with console handler?
    # The code prints to stdout/stderr on error
    captured = capsys.readouterr()
    assert "Failed to create log file" in captured.out
    
    # Should still have console handler
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
