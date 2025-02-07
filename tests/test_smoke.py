from http import HTTPStatus

import requests


def test_status(app_url):
    """Проверка доступности сервиса"""
    response = requests.get(f'{app_url}/status')
    assert response.status_code == HTTPStatus.OK, \
        f'Неожиданный код ответа, ошибка {response.text}'
    assert response.json()['database'] is True


def test_get_users(app_url):
    """Проверка доступности списка пользователей"""
    response = requests.get(f'{app_url}/api/users/')
    assert response.status_code == HTTPStatus.OK, \
        f'Не удалось получить список пользователей, ошибка {response.text}'
