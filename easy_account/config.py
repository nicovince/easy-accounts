"""Configuration file handling for easy-account."""

from pathlib import Path

# Use tomllib for Python 3.11+ or tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


class ConfigError(Exception):
    """Raised when there's an error with the configuration."""

    pass


def find_config_file() -> Path | None:
    """Find the .easy-account.toml file in the current directory.

    Returns:
        Path to the config file if found, None otherwise.
    """
    config_path = Path(".easy-account.toml")
    if config_path.exists():
        return config_path
    return None


def load_config(config_path: Path | None = None) -> dict:
    """Load configuration from TOML file.

    Args:
        config_path: Path to the config file. If None, searches in current directory.

    Returns:
        Dictionary containing the configuration.

    Raises:
        ConfigError: If config file is not found or has invalid format.
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None:
        raise ConfigError("Configuration file .easy-account.toml not found in current directory")

    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        return config
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_path}")
    except Exception as e:
        raise ConfigError(f"Failed to parse configuration file {config_path}: {e}")


def get_months(config: dict | None = None) -> list[str]:
    """Get list of valid months from config.

    Args:
        config: Configuration dictionary. If None, loads from file.

    Returns:
        List of month names.

    Raises:
        ConfigError: If months are not defined in config.
    """
    if config is None:
        config = load_config()

    try:
        # Handle nested structure: config["months"]["months"]
        months = config.get("months", {})
        if isinstance(months, dict):
            months = months.get("months", [])

        if not months:
            raise ConfigError("No months defined in configuration file")
        return list(months)
    except Exception as e:
        raise ConfigError(f"Failed to read months from config: {e}")


def get_categories(config: dict | None = None) -> list[str]:
    """Get list of valid categories from config.

    Args:
        config: Configuration dictionary. If None, loads from file.

    Returns:
        List of category names.

    Raises:
        ConfigError: If categories are not defined in config.
    """
    if config is None:
        config = load_config()

    try:
        # Handle nested structure: config["categories"]["categories"]
        categories = config.get("categories", {})
        if isinstance(categories, dict):
            categories = categories.get("categories", [])

        if not categories:
            raise ConfigError("No categories defined in configuration file")
        return list(categories)
    except Exception as e:
        raise ConfigError(f"Failed to read categories from config: {e}")


def get_users(config: dict | None = None) -> list[str]:
    """Get list of valid users from config.

    Args:
        config: Configuration dictionary. If None, loads from file.

    Returns:
        List of user names, or empty list if users not defined.

    Raises:
        ConfigError: If there's an error reading users from config.
    """
    if config is None:
        try:
            config = load_config()
        except ConfigError:
            # No config file, return empty list
            return []

    try:
        # Handle nested structure: config["users"]["users"]
        users = config.get("users", {})
        if isinstance(users, dict):
            users = users.get("users", [])

        return list(users) if users else []
    except Exception as e:
        raise ConfigError(f"Failed to read users from config: {e}")


def create_example_config(path: Path = Path(".easy-account.toml")) -> None:
    """Create an example configuration file.

    Args:
        path: Path where to create the example config file.
    """
    example_config = """# Easy Account Configuration
# This file defines the months, categories, and users for your accounting spreadsheet

[months]
# List of months for autocomplete
months = [
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
]

[categories]
# List of spending categories for autocomplete
categories = [
    "groceries",
    "utilities",
    "rent",
    "transport",
    "entertainment",
    "healthcare",
    "dining",
    "shopping",
]

[users]
# List of users for multi-user accounts (optional)
# Remove this section if you don't use multi-user accounts
users = [
    "alice",
    "bob",
    "charlie",
]
"""
    with open(path, "w") as f:
        f.write(example_config)
