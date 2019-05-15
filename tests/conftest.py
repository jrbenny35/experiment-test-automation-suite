import os
import typing

import pytest


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--experiment",
        action="store",
        default=None,
        help="path to experiment XPI needing validation",
    ),
    parser.addoption(
        "--run-old-firefox",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    )


@pytest.fixture
def firefox_options(
    pytestconfig: typing.Any, firefox_options: typing.Any
) -> typing.Any:
    if pytestconfig.getoption("--run-old-firefox"):
        binary = os.path.abspath("utilities/firefox-old-nightly/firefox/firefox-bin")
        firefox_options.binary = binary
    firefox_options.set_preference("extensions.install.requireBuiltInCerts", False)
    firefox_options.set_preference("ui.popup.disable_autohide", True)
    firefox_options.set_preference("xpinstall.signatures.required", False)
    firefox_options.set_preference("extensions.webapi.testing", True)
    firefox_options.set_preference("extensions.legacy.enabled", True)
    firefox_options.set_preference("browser.tabs.remote.autostart", True)
    firefox_options.set_preference("browser.tabs.remote.autostart.1", True)
    firefox_options.set_preference("browser.tabs.remote.autostart.2", True)
    firefox_options.set_preference("devtools.chrome.enabled", True)
    firefox_options.set_preference("devtools.debugger.remote-enabled", True)
    firefox_options.set_preference("devtools.debugger.prompt-connection", False)
    firefox_options.set_preference("shieldStudy.logLevel", "All")
    firefox_options.add_argument("-headless")
    firefox_options.log.level = "trace"
    return firefox_options


@pytest.fixture
def firefox_startup_time(firefox: typing.Any) -> typing.Any:
    """Startup with no extension installed"""
    return firefox.selenium.execute_script(
        """
        perfData = window.performance.timing 
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )


@pytest.fixture
def addon_ids():
    return []


@pytest.fixture
def selenium(pytestconfig: typing.Any, selenium: typing.Any, addon_ids: list) -> typing.Any:
    """Setup Selenium"""
    addon = pytestconfig.getoption("--experiment")
    addon_id = selenium.install_addon(os.path.abspath(addon))
    addon_ids.append(addon_id)
    return selenium
