import os

import dotenv
import pytest


pytest_plugins = [
    'tests.fixtures'
]


@pytest.fixture(scope="session", autouse=True)
def envs():
    dotenv.load_dotenv()


@pytest.fixture(scope="module")
def app_url():
    return os.getenv("APP_URL")
