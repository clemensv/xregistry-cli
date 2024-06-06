"""Utility class for URL operations."""

from typing import Optional
import urllib.parse

from xregistry.cli import logger


class URLUtils:
    """Utility class for URL operations."""

    @staticmethod
    def get_url_host(url: str) -> Optional[str]:
        """Get the host from a URL."""
        logger.debug("Getting host from URL: %s", url)
        return urllib.parse.urlparse(url).hostname

    @staticmethod
    def get_url_path(url: str) -> str:
        """Get the path from a URL."""
        logger.debug("Getting path from URL: %s", url)
        return urllib.parse.urlparse(url).path

    @staticmethod
    def get_url_scheme(url: str) -> str:
        """Get the scheme from a URL."""
        logger.debug("Getting scheme from URL: %s", url)
        return urllib.parse.urlparse(url).scheme

    @staticmethod
    def get_url_port(url: str) -> str:
        """Get the port from a URL."""
        logger.debug("Getting port from URL: %s", url)
        return str(urllib.parse.urlparse(url).port)