"""Configuration management for WCAG Scanner."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BrowserConfig(BaseModel):
    """Browser configuration settings."""
    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout: int = Field(default=30000, description="Browser timeout in milliseconds")


class ScanConfig(BaseModel):
    """Scan configuration settings."""
    timeout: int = Field(default=120, description="Overall scan timeout in seconds")
    wcag_level: str = Field(default="AA", description="WCAG conformance level (A, AA, AAA)")
    tools: list[str] = Field(
        default=["axe", "pa11y", "lighthouse", "html_validator", "contrast"],
        description="List of tools to run"
    )


class ServerConfig(BaseModel):
    """Server configuration settings."""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")


class Config(BaseModel):
    """Main configuration class."""
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    scan: ScanConfig = Field(default_factory=ScanConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    log_level: str = Field(default="INFO", description="Logging level")
    wave_api_key: Optional[str] = Field(default=None, description="WAVE API key")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            browser=BrowserConfig(
                headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
                timeout=int(os.getenv("BROWSER_TIMEOUT", "30000"))
            ),
            scan=ScanConfig(
                timeout=int(os.getenv("SCAN_TIMEOUT", "120")),
                wcag_level=os.getenv("DEFAULT_WCAG_LEVEL", "AA"),
            ),
            server=ServerConfig(
                host=os.getenv("HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", "8000"))
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            wave_api_key=os.getenv("WAVE_API_KEY")
        )


# Global configuration instance
config = Config.from_env()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_templates_dir() -> Path:
    """Get the templates directory."""
    return get_project_root() / "templates"
