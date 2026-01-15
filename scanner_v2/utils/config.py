"""Configuration management for WCAG Scanner V2."""

import os
from pathlib import Path
from typing import List, Union, Optional
import yaml
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from scanner_v2.utils.exceptions import ConfigFileNotFoundError, InvalidConfigError


class ServerConfig(BaseSettings):
    """Server configuration."""

    model_config = ConfigDict(extra='ignore')

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = ConfigDict(extra="ignore")

    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    database_name: str = "wcag_scanner"


class QueueConfig(BaseSettings):
    """Queue configuration."""

    model_config = ConfigDict(extra="ignore")

    worker_count: int = 5
    max_queue_size: int = 1000
    job_timeout: int = 300  # seconds


class ScanningConfig(BaseSettings):
    """Scanning configuration."""

    model_config = ConfigDict(extra="ignore")

    default_max_depth: int = 3
    default_max_pages: int = 100
    default_wait_time: int = 2000  # ms
    default_wcag_level: str = "AA"
    default_scanners: List[str] = ["axe", "pa11y", "lighthouse"]
    page_timeout: int = 30000  # ms
    screenshot_enabled: bool = True


class BrowserConfig(BaseSettings):
    """Browser configuration."""

    model_config = ConfigDict(extra="ignore")

    headless: bool = True
    timeout: int = 30000


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = ConfigDict(extra="ignore")

    level: str = "INFO"
    format: str = "standard"  # json or standard


class SecurityConfig(BaseSettings):
    """Security configuration."""

    model_config = ConfigDict(extra="ignore")

    jwt_secret: str = Field(default="change-this-secret-key-in-production")
    jwt_expiry: int = 3600  # seconds
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]


class Config(BaseSettings):
    """Main configuration."""

    model_config = ConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    queue: QueueConfig = Field(default_factory=QueueConfig)
    scanning: ScanningConfig = Field(default_factory=ScanningConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)



def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Config object

    Raises:
        ConfigFileNotFoundError: If config file not found
        InvalidConfigError: If config file is invalid
    """
    if config_path is None:
        # Default to scanner_v2/config.yaml
        config_path = Path(__file__).parent.parent / "config.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigFileNotFoundError(
            f"Config file not found: {config_path}",
            {"path": str(config_path)}
        )

    try:
        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f)

        # Replace environment variables in YAML values
        yaml_config = _replace_env_vars(yaml_config)

        # Create config objects
        config = Config(
            server=ServerConfig(**yaml_config.get("server", {})),
            database=DatabaseConfig(**yaml_config.get("database", {})),
            queue=QueueConfig(**yaml_config.get("queue", {})),
            scanning=ScanningConfig(**yaml_config.get("scanning", {})),
            browser=BrowserConfig(**yaml_config.get("browser", {})),
            logging=LoggingConfig(**yaml_config.get("logging", {})),
            security=SecurityConfig(**yaml_config.get("security", {})),
        )

        return config

    except Exception as e:
        raise InvalidConfigError(
            f"Failed to parse config file: {e}",
            {"path": str(config_path), "error": str(e)}
        )


def _replace_env_vars(config_dict: dict) -> dict:
    """
    Replace environment variable references in config values.

    Supports ${VAR} and ${VAR:-default} syntax.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Dictionary with environment variables replaced
    """
    import re

    def replace_value(value):
        if isinstance(value, str):
            # Match ${VAR} or ${VAR:-default}
            pattern = r'\$\{([^}:]+)(?::-(.*?))?\}'

            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2)
                return os.getenv(var_name, default_value or "")

            return re.sub(pattern, replacer, value)
        elif isinstance(value, dict):
            return {k: replace_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_value(item) for item in value]
        else:
            return value

    return replace_value(config_dict)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: Config) -> None:
    """
    Set global configuration instance.

    Args:
        config: Config instance
    """
    global _config
    _config = config
