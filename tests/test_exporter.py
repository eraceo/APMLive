import os
import json
import threading
import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.core.exporter import DataExporter


# Mock logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch("src.core.exporter.logger") as mock:
        yield mock


@pytest.fixture
def mock_data_dir(tmp_path):
    return str(tmp_path)


def test_exporter_init_default(mock_data_dir):
    """Test initialization with default directory (mocked LOCALAPPDATA)."""
    with patch("os.getenv", return_value=mock_data_dir):
        exporter = DataExporter()
        assert exporter.data_dir == os.path.join(mock_data_dir, "APMLive")
        assert os.path.exists(exporter.data_dir)


def test_exporter_init_no_localappdata(mock_data_dir):
    """Test initialization without LOCALAPPDATA (fallback to cwd)."""
    with patch("os.getenv", return_value=None):
        with patch("os.getcwd", return_value=mock_data_dir):
            exporter = DataExporter()
            assert exporter.data_dir == os.path.join(mock_data_dir, "APMLive_Data")


def test_exporter_init_custom_dir(mock_data_dir):
    """Test initialization with custom directory."""
    custom_dir = os.path.join(mock_data_dir, "Custom")
    exporter = DataExporter(data_dir=custom_dir)
    assert exporter.data_dir == custom_dir
    assert os.path.exists(custom_dir)


def test_load_settings_success(mock_data_dir):
    """Test loading settings from a valid JSON file."""
    exporter = DataExporter(data_dir=mock_data_dir)
    settings = {"txt_export": {"apm": False, "timestamp": True}}

    with open(exporter.settings_file, "w") as f:
        json.dump(settings, f)

    exporter.load_settings()
    assert exporter.txt_settings["apm"] is False
    assert exporter.txt_settings["timestamp"] is True
    assert exporter.txt_settings["total_actions"] is True  # Default remains


def test_load_settings_file_not_found(mock_data_dir):
    """Test loading settings when file does not exist."""
    exporter = DataExporter(data_dir=mock_data_dir)
    # Ensure file doesn't exist
    if os.path.exists(exporter.settings_file):
        os.remove(exporter.settings_file)

    exporter.load_settings()
    # Should keep defaults
    assert exporter.txt_settings["apm"] is True


def test_load_settings_invalid_json(mock_data_dir, mock_logger):
    """Test loading settings with invalid JSON content."""
    exporter = DataExporter(data_dir=mock_data_dir)
    with open(exporter.settings_file, "w") as f:
        f.write("invalid json")

    exporter.load_settings()
    # Should log error and keep defaults
    mock_logger.error.assert_called()
    assert exporter.txt_settings["apm"] is True


def test_save_settings_success(mock_data_dir):
    """Test saving settings to JSON file."""
    exporter = DataExporter(data_dir=mock_data_dir)
    exporter.txt_settings["apm"] = False
    exporter.save_settings()

    assert os.path.exists(exporter.settings_file)
    with open(exporter.settings_file, "r") as f:
        data = json.load(f)
        assert data["txt_export"]["apm"] is False


def test_save_settings_error(mock_data_dir, mock_logger):
    """Test error handling during save_settings."""
    exporter = DataExporter(data_dir=mock_data_dir)

    # Mock open to raise IOError
    with patch("builtins.open", side_effect=IOError("Write error")):
        exporter.save_settings()

    mock_logger.error.assert_called()


def test_update_settings(mock_data_dir):
    """Test updating settings."""
    exporter = DataExporter(data_dir=mock_data_dir)
    new_settings = {"apm": False, "actions_per_second": True}

    exporter.update_settings(new_settings)

    assert exporter.txt_settings["apm"] is False
    assert exporter.txt_settings["actions_per_second"] is True
    # Should have saved to file
    assert os.path.exists(exporter.settings_file)


def test_export_threading(mock_data_dir):
    """Test that export runs in a separate thread."""
    exporter = DataExporter(data_dir=mock_data_dir)
    metrics = {"test": 1}

    with patch("threading.Thread") as mock_thread:
        exporter.export(metrics)
        mock_thread.assert_called_once()
        args = mock_thread.call_args[1]
        assert args["target"] == exporter._write_files
        assert args["args"] == (metrics,)
        assert args["daemon"] is True


def test_write_files_success(mock_data_dir):
    """Test writing files with various settings."""
    exporter = DataExporter(data_dir=mock_data_dir)
    # Enable all settings for full coverage
    exporter.txt_settings = {
        "apm": True,
        "total_actions": True,
        "session_time": True,
        "avg_apm": True,
        "actions_per_second": True,
        "timestamp": True,
    }

    metrics = {
        "current_apm": 120,
        "total_actions": 500,
        "session_time": 3665,  # 1h 1m 5s
        "avg_apm": 100,
        "aps": 2.5,
        "timestamp": 1678886400,
    }

    exporter._write_files(metrics)

    # Check JSON file
    assert os.path.exists(exporter.json_file)
    with open(exporter.json_file, "r") as f:
        json_data = json.load(f)
        assert json_data["current_apm"] == 120

    # Check TXT file
    assert os.path.exists(exporter.output_file)
    with open(exporter.output_file, "r") as f:
        content = f.read()
        assert "TS: 1678886400" in content
        assert "APM: 120" in content
        assert "AVG: 100" in content
        assert "APS: 2.5" in content
        assert "Total: 500" in content
        assert "Time: 01:01:05" in content


def test_write_files_partial_settings(mock_data_dir):
    """Test writing files with partial settings disabled."""
    exporter = DataExporter(data_dir=mock_data_dir)
    exporter.txt_settings = {
        "apm": True,
        "total_actions": False,
        "session_time": False,
        "avg_apm": False,
        "actions_per_second": False,
        "timestamp": False,
    }

    metrics = {"current_apm": 60}
    exporter._write_files(metrics)

    with open(exporter.output_file, "r") as f:
        content = f.read()
        assert "APM: 60" in content
        assert "Total:" not in content
        assert "Time:" not in content


def test_write_files_error(mock_data_dir, mock_logger):
    """Test error handling during file writing."""
    exporter = DataExporter(data_dir=mock_data_dir)
    metrics = {}

    # Mock open to raise IOError
    with patch("builtins.open", side_effect=IOError("Write error")):
        exporter._write_files(metrics)

    mock_logger.error.assert_called()
