from ast import literal_eval
from http import HTTPStatus

import pytest
import requests

from faker import Faker
from app.models.User import UserCreate, User


def generate_user() -> UserCreate:
    fake = Faker('ru_RU')
    return UserCreate(
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        avatar=fake.uri()
    )


@pytest.fixture
def user_data_for_create() -> dict:
    return literal_eval(generate_user().model_dump_json())


@pytest.fixture(params=[{'delete': True}])
def create_user(app_url, user_data_for_create, request) -> User:
    response = requests.post(
        f"{app_url}/api/users/",
        json=user_data_for_create
    )
    assert response.status_code == HTTPStatus.CREATED
    user_created = User(**response.json())

    yield user_created

    if request.param.get('delete') is False and request.session.testsfailed == 0:
        pass
    else:
        response_del = requests.delete(f"{app_url}/api/users/{user_created.id}")
        assert response_del.status_code == HTTPStatus.OK
