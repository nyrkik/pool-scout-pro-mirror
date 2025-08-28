# src/core/browser.py
from __future__ import annotations

import os
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) "
    "Gecko/20100101 Firefox/115.0"
)
DEFAULT_ACCEPT = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,*/*;q=0.8"
)
DEFAULT_LANG = "en-US,en;q=0.5"


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def create_driver(
    headless: Optional[bool] = None,
    user_agent: Optional[str] = None,
    accept_header: Optional[str] = None,
    accept_language: Optional[str] = None,
    page_load_timeout: Optional[int] = None,
    implicit_wait: int = 0,
) -> WebDriver:
    """
    Create and return a configured Firefox WebDriver.

    If SELENIUM_REMOTE_URL is set, connect to the running selenium-firefox
    container via Remote WebDriver. Otherwise, fall back to local Firefox.
    """
    # Resolve runtime options (env -> params -> defaults)
    if headless is None:
        headless = _env_bool("PSP_HEADLESS", True)
    ua = user_agent or os.getenv("PSP_USER_AGENT", DEFAULT_UA)
    accept = accept_header or os.getenv("PSP_ACCEPT", DEFAULT_ACCEPT)
    lang = accept_language or os.getenv("PSP_ACCEPT_LANG", DEFAULT_LANG)

    try:
        plt_env = int(os.getenv("PSP_PAGELOAD_TIMEOUT", ""))
    except ValueError:
        plt_env = None
    if page_load_timeout is None:
        page_load_timeout = plt_env if plt_env is not None else 60

    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")

    # Stability prefs
    options.set_preference("browser.tabs.remote.autostart", True)
    options.set_preference("toolkit.telemetry.enabled", False)
    options.set_preference("datareporting.healthreport.uploadEnabled", False)
    options.set_preference("dom.ipc.processCount", 4)

    # Browser-like headers (match your successful curl)
    options.set_preference("general.useragent.override", ua)
    options.set_preference("intl.accept_languages", lang)
    options.set_preference("network.http.accept.default", accept)

    remote_url = os.getenv("SELENIUM_REMOTE_URL")
    logger.info(
        "Creating %s Firefox driver | headless=%s, timeout=%ss",
        "REMOTE" if remote_url else "LOCAL",
        headless,
        page_load_timeout,
    )

    if remote_url:
        # ✅ Use Selenium Grid / standalone container
        driver = webdriver.Remote(command_executor=remote_url, options=options)
    else:
        # ⚠️ Local mode requires writable cache & system firefox/geckodriver
        driver = webdriver.Firefox(options=options)

    # Timeouts
    try:
        driver.set_page_load_timeout(page_load_timeout)
    except Exception as e:
        logger.warning("Failed to set page_load_timeout(%s): %s", page_load_timeout, e)
    if implicit_wait:
        driver.implicitly_wait(implicit_wait)

    # Log effective UA
    try:
        effective_ua = driver.execute_script("return navigator.userAgent")
        logger.info("Effective userAgent: %s", effective_ua)
    except Exception:
        pass

    return driver
    
# --- Back-compat shim so existing imports keep working -----------------------
class BrowserManager:
    @staticmethod
    def create_driver(
        headless: Optional[bool] = None,
        user_agent: Optional[str] = None,
        accept_header: Optional[str] = None,
        accept_language: Optional[str] = None,
        page_load_timeout: Optional[int] = None,
        implicit_wait: int = 0,
    ) -> WebDriver:
        # Delegate to the module-level function
        return create_driver(
            headless=headless,
            user_agent=user_agent,
            accept_header=accept_header,
            accept_language=accept_language,
            page_load_timeout=page_load_timeout,
            implicit_wait=implicit_wait,
        )

__all__ = ["create_driver", "BrowserManager"]


