import os
import re
import shutil
import typing
import json
from zipfile import ZipFile

import pytest

from tests.toolbar import ToolBar


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
def setup_profile(pytestconfig: typing.Any, request: typing.Any) -> typing.Any:
    """"Fixture to create a copy of the profile to use within the test."""
    if pytestconfig.getoption("--run-old-firefox"):
        shutil.copytree(
            os.path.abspath("utilities/klaatu-profile-old-base"),
            os.path.abspath("utilities/klaatu-profile"),
        )
        return f'{os.path.abspath("utilities/klaatu-profile")}'
    if request.node.get_closest_marker("reuse_profile") and not pytestconfig.getoption(
        "--run-old-firefox"
    ):
        # shutil.copytree(
        #    os.path.abspath("utilities/klaatu-profile-current-base"),
        #    os.path.abspath("utilities/klaatu-profile-current-nightly"),
        # )
        return f'{os.path.abspath("utilities/klaatu-profile-1")}'


@pytest.fixture
def firefox_options(
    setup_profile: typing.Any,
    pytestconfig: typing.Any,
    firefox_options: typing.Any,
    experiment_widget_id: typing.Any,
    request: typing.Any,
) -> typing.Any:
    """Setup Firefox"""
    firefox_options.log.level = "trace"
    if pytestconfig.getoption("--run-old-firefox"):
        if request.node.get_closest_marker(
            "update_test"
        ):  # disable test needs different firefox
            binary = os.path.abspath(
                "utilities/firefox-old-nightly-disable-test/firefox/firefox-bin"
            )
            firefox_options.binary = binary
            firefox_options.add_argument("-profile")
            firefox_options.add_argument(
                f'{os.path.abspath("utilities/klaatu-profile-disable-test")}'
            )
        else:
            binary = os.path.abspath(
                "utilities/firefox-old-nightly/firefox/firefox-bin"
            )
            firefox_options.binary = binary
            firefox_options.add_argument("-profile")
            firefox_options.add_argument(setup_profile)
    if request.node.get_closest_marker("reuse_profile") and not pytestconfig.getoption(
        "--run-old-firefox"
    ):
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(setup_profile)
    firefox_options.set_preference("extensions.install.requireBuiltInCerts", False)
    # firefox_options.set_preference("ui.popup.disable_autohide", True)
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
    firefox_options.set_preference(
        f"extensions.{experiment_widget_id}.test.expired", True
    )
    # firefox_options.add_argument("-headless")
    yield firefox_options
    # remove old profile
    # if (
    #    request.node.get_closest_marker("reuse_profile")
    #    and not pytestconfig.getoption("--run-old-firefox")
    #    or pytestconfig.getoption("--run-old-firefox")
    # ):
        # shutil.rmtree(setup_profile)


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
def experiment_widget_id(pytestconfig: typing.Any, request: typing.Any) -> typing.Any:
    """Experiment's ID"""
    if not request.node.get_closest_marker("expire_experiment"):
        return

    zip_file = os.path.abspath(pytestconfig.getoption("--experiment"))
    with ZipFile(zip_file) as myzip:
        with myzip.open("manifest.json") as myfile:
            manifest = json.load(myfile)
    widget_id = (
        manifest["applications"]["gecko"]["id"].replace("@", "_").replace(".", "_")
    )
    if request.config.option.run_old_firefox:
        with open("utilities/klaatu-profile/user.js", "a") as f:
            f.write(f'\nuser_pref("extensions.{widget_id}.test.expired", true);\n')
    return f"{widget_id}"


@pytest.fixture
def addon_ids() -> dict:
    return {}


@pytest.fixture
def selenium(
    pytestconfig: typing.Any, selenium: typing.Any, addon_ids: dict
) -> typing.Any:
    """Setup Selenium"""
    addon = pytestconfig.getoption("--experiment")
    addon_name = selenium.install_addon(os.path.abspath(addon))
    with selenium.context(selenium.CONTEXT_CHROME):
        addon_id = selenium.execute_script(
            """
            var Cu = Components.utils;
            const {WebExtensionPolicy} = Cu.getGlobalForObject(
                Cu.import("resource://gre/modules/Extension.jsm", this)
            );

            return WebExtensionPolicy.getByID(arguments[0]).mozExtensionHostname;
        """,
            addon_name,
        )
    addon_ids[addon_name] = addon_id
    return selenium
