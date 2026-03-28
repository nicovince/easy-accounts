"""Configuration file handling for easy-account."""

from pathlib import Path

from easy_account.account import AccountSpreadsheet

# Use tomllib for Python 3.11+ or tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


class ConfigError(Exception):
    """Raised when there's an error with the configuration."""

    pass


class ConfigValidationError(Exception):
    """Raised when config entries don't match the spreadsheet."""

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


def validate_config_against_spreadsheet(
    config: dict,
    spreadsheet_path: str,
    sheet_name: str | None = None,
) -> None:
    """Validate that config entries exist in the spreadsheet.

    Args:
        config: Configuration dictionary.
        spreadsheet_path: Path to the spreadsheet file.
        sheet_name: Optional sheet name to validate against.

    Raises:
        ConfigValidationError: If any config entry doesn't exist in the spreadsheet.
    """
    account = AccountSpreadsheet(spreadsheet_path)
    if sheet_name:
        account.active_sheet = sheet_name

    errors = []

    months = get_months(config)
    spreadsheet_months = set(account.get_spreadsheet_months())
    for month in months:
        if month not in spreadsheet_months:
            errors.append(f"Month '{month}' not found in spreadsheet")

    categories = get_categories(config)
    spreadsheet_categories = set(account.get_spreadsheet_categories())
    for category in categories:
        if category not in spreadsheet_categories:
            errors.append(f"Category '{category}' not found in spreadsheet")

    users = get_users(config)
    if users:
        spreadsheet_users = set(account.get_spreadsheet_users())
        for user in users:
            if user not in spreadsheet_users:
                errors.append(f"User '{user}' not found in spreadsheet")

    if errors:
        raise ConfigValidationError("\n".join(errors))


def get_spreadsheet_users(spreadsheet_path: str, sheet_name: str | None = None) -> list[str]:
    """Get list of users from spreadsheet.

    Args:
        spreadsheet_path: Path to the spreadsheet file.
        sheet_name: Optional sheet name to extract from.

    Returns:
        List of user names found in the spreadsheet, or empty list if no users.
    """
    account = AccountSpreadsheet(spreadsheet_path)
    if sheet_name:
        account.active_sheet = sheet_name
    return account.get_spreadsheet_users()


def is_multiuser_spreadsheet(spreadsheet_path: str, sheet_name: str | None = None) -> bool:
    """Check if spreadsheet is multi-user based on merged cells in the month row.

    Args:
        spreadsheet_path: Path to the spreadsheet file.
        sheet_name: Optional sheet name to check.

    Returns:
        True if spreadsheet has merged cells in the month row (multi-user).
    """
    account = AccountSpreadsheet(spreadsheet_path)
    if sheet_name:
        account.active_sheet = sheet_name
    return account.is_multiuser()


def create_config_from_spreadsheet(
    spreadsheet_path: str,
    sheet_name: str | None = None,
    output_path: Path = Path(".easy-account.toml"),
) -> None:
    """Create a configuration file from an existing spreadsheet.

    Args:
        spreadsheet_path: Path to the spreadsheet file.
        sheet_name: Optional sheet name to extract from.
        output_path: Path where to create the config file.
    """
    account = AccountSpreadsheet(spreadsheet_path)
    if sheet_name:
        account.active_sheet = sheet_name

    months = account.get_spreadsheet_months()
    categories = account.get_spreadsheet_categories()
    users = account.get_spreadsheet_users() if account.is_multiuser() else []

    config_lines = ["# Easy Account Configuration\n"]

    config_lines.append("[months]\nmonths = [\n")
    for month in months:
        config_lines.append(f'    "{month}",\n')
    config_lines.append("]\n\n")

    config_lines.append("[categories]\ncategories = [\n")
    for category in categories:
        config_lines.append(f'    "{category}",\n')
    config_lines.append("]\n")

    if users:
        config_lines.append("\n[users]\nusers = [\n")
        for user in users:
            config_lines.append(f'    "{user}",\n')
        config_lines.append("]\n")

    with open(output_path, "w") as f:
        f.writelines(config_lines)
