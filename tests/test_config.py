"""Tests for config module."""

import os
from pathlib import Path

import pytest

from easy_account.config import (
    ConfigError,
    create_example_config,
    find_config_file,
    get_categories,
    get_months,
    get_users,
    load_config,
)


@pytest.fixture
def tmp_path_cwd(tmp_path):
    """Set current working directory to tmp_path and restore on teardown"""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


def test_find_config_file_exists(tmp_path_cwd):
    """Test finding config file when it exists."""
    config_path = tmp_path_cwd / ".easy-account.toml"
    config_path.touch()
    found = find_config_file()
    assert found.name == ".easy-account.toml"


def test_find_config_file_not_exists(tmp_path_cwd):
    """Test finding config file when it doesn't exist."""
    found = find_config_file()
    assert found is None


def test_create_example_config(tmp_path):
    """Test creating example config file."""
    config_path = tmp_path / ".easy-account.toml"
    create_example_config(config_path)

    assert config_path.exists()
    content = config_path.read_text()
    assert "months" in content
    assert "categories" in content
    assert "janvier" in content
    assert "groceries" in content


def test_load_config_valid(tmp_path):
    """Test loading a valid config file."""
    config_path = tmp_path / ".easy-account.toml"
    create_example_config(config_path)

    config = load_config(config_path)
    assert "months" in config
    assert "categories" in config


def test_load_config_not_found():
    """Test loading config file when it doesn't exist."""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(Path("/nonexistent/.easy-account.toml"))


def test_load_config_invalid_toml(tmp_path):
    """Test loading invalid TOML file."""
    config_path = tmp_path / ".easy-account.toml"
    config_path.write_text("invalid [toml")

    with pytest.raises(ConfigError, match="Failed to parse configuration"):
        load_config(config_path)


def test_get_months_valid(tmp_path):
    """Test getting months from valid config."""
    config_path = tmp_path / ".easy-account.toml"
    create_example_config(config_path)

    config = load_config(config_path)
    months = get_months(config)

    assert "janvier" in months
    assert "decembre" in months
    assert len(months) == 12


def test_get_months_without_config_file(tmp_path_cwd):
    """Test getting months when config file is not in current directory."""
    with pytest.raises(ConfigError, match="not found in current directory"):
        get_months()


def test_get_categories_valid(tmp_path):
    """Test getting categories from valid config."""
    config_path = tmp_path / ".easy-account.toml"
    create_example_config(config_path)

    config = load_config(config_path)
    categories = get_categories(config)

    assert "groceries" in categories
    assert "shopping" in categories


def test_get_categories_without_config_file(tmp_path_cwd):
    """Test getting categories when config file is not in current directory."""
    with pytest.raises(ConfigError, match="not found in current directory"):
        get_categories()


def test_config_with_custom_months_categories(tmp_path):
    """Test config with custom months and categories."""
    config_path = tmp_path / ".easy-account.toml"
    config_content = """
[months]
months = ["Q1", "Q2", "Q3", "Q4"]

[categories]
categories = ["salary", "expenses", "savings"]
"""
    config_path.write_text(config_content)

    config = load_config(config_path)
    months = get_months(config)
    categories = get_categories(config)

    assert months == ["Q1", "Q2", "Q3", "Q4"]
    assert categories == ["salary", "expenses", "savings"]


def test_get_users_valid(tmp_path):
    """Test getting users from valid config."""
    config_path = tmp_path / ".easy-account.toml"
    create_example_config(config_path)

    config = load_config(config_path)
    users = get_users(config)

    assert "alice" in users
    assert "bob" in users
    assert "charlie" in users


def test_get_users_empty_when_not_defined(tmp_path):
    """Test getting users when not defined in config."""
    config_path = tmp_path / ".easy-account.toml"
    config_content = """
[months]
months = ["january"]

[categories]
categories = ["food"]
"""
    config_path.write_text(config_content)

    config = load_config(config_path)
    users = get_users(config)

    assert users == []


def test_get_users_without_config_file(tmp_path_cwd):
    """Test getting users when config file doesn't exist returns empty list."""
    users = get_users()
    assert users == []


def test_config_with_custom_users(tmp_path):
    """Test config with custom users."""
    config_path = tmp_path / ".easy-account.toml"
    config_content = """
[months]
months = ["january"]

[categories]
categories = ["food"]

[users]
users = ["john", "jane", "jack"]
"""
    config_path.write_text(config_content)

    config = load_config(config_path)
    users = get_users(config)

    assert users == ["john", "jane", "jack"]
