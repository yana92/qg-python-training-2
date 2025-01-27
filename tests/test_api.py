import math
from http import HTTPStatus

from pytest import mark, fixture

import requests
from models.User import User, Users


@fixture
def users(app_url):
    response = requests.get(f"{app_url}/api/users/")
    assert response.status_code == HTTPStatus.OK
    return response.json()


def test_users(app_url):
    response = requests.get(f'{app_url}/api/users/')
    assert response.status_code == HTTPStatus.OK
    Users.model_validate(response.json())


def test_get_users_pagination(app_url, users):
    """Проверка пагинации

    Запросить список пользователей с параметром size

    Проверить:
    Схема ответа валидна
    Количество пользователей в ответе соответсвует заданному колличеству в size
    Значения полей total, page, pages соответсвуют ожидаемым значениям

    """
    total = len(users['items'])
    size = total - 1
    pages = math.ceil(total / size)
    response = requests.get(url=f'{app_url}/api/users/',
                            params={'size': size})
    assert response.status_code == HTTPStatus.OK, \
        f'Неожиданный код ответа, ошибка {response.text}'
    assert Users.model_validate(response.json())
    items = response.json()['items']
    assert len(items) == size, \
        'Количество пользователей в ответе отличается от заданного'
    assert response.json()['size'] == size, 'Size в ответе отличается от заданного'
    assert response.json()['page'] == 1, \
        'Ожидалось, что в ответе вернется первая страница списка'
    assert response.json()['total'] == total, \
        'Значение поля total в ответе не соответсвует общему количество пользователей'
    assert response.json()['pages'] == pages, \
        'Значение поля pages в ответе не соответвует общему колличеству страниц'


@mark.parametrize('page_size', [5, 11, 12, 13])
def test_get_users_all_pagination(app_url, users, page_size):
    """Проверка пагинации

    Запросить постранично список пользователей с различным значением size

    Проверить:
    Схема ответа валидна
    Количество пользователей в ответе соответсвует заданному колличеству в size
    Каждый раз возвращаются уникальные пользователи
    Значения полей size, total, page, pages соответсвуют ожидаемым
    Состав пользователей в ответе соответствует ожидаемому

    """
    total = len(users['items'])
    page_count = math.ceil(total / page_size)
    last_page_count = total - (page_size * (page_count - 1))
    user_ids = []
    for i in range(1, page_count+1):
        response = requests.get(url=f'{app_url}/api/users/',
                                params={'size': page_size, 'page': i})
        assert response.status_code == HTTPStatus.OK, \
            f'Не удалось получить список пользователей, ошибка {response.text}'
        assert Users.model_validate(response.json())
        result = response.json()
        items = result['items']
        if i < page_count:
            assert len(items) == page_size, \
                'Количество пользователей в ответе отличается от запрошенного'
        else:
            assert len(items) == last_page_count, \
                'Колличество пользователей на последней страницей не соотвтевует ожидаемому'
        for item in items:
            assert item['id'] not in user_ids, \
                f'Один и тот же пользователь c id {item["id"]} вернулся дважды'
            user_ids.append(item['id'])
            assert result['page'] == i, 'Номер страницы в ответе отличается от ожидаемого'
            assert result['pages'] == page_count, 'В ответе вернулось некорректное число страниц'
            assert result['size'] == page_size, \
                'Значение поля size в ответе оличается от запрошенного'
            assert result['total'] == total, \
                'Значение поля total в ответе не соответвует общему числа пользователей'
    assert len(user_ids) == len(users['items']), \
        'Колличество пользователей в ответе не соответствует ожидаемому'
    users_ids = [u['id'] for u in users['items']]
    assert set(user_ids) == set(users_ids), 'Состав пользователей в ответе отличается от ожидаемого'


def test_users_no_duplicates(users):
    users_ids = [user["id"] for user in users['items']]
    assert len(users_ids) == len(set(users_ids))


@mark.parametrize('user_id', [1, 6, 12])
def test_user(app_url, user_id):
    response = requests.get(f'{app_url}/api/users/{user_id}')
    assert response.status_code == HTTPStatus.OK
    user = response.json()
    User.model_validate(user)


@mark.parametrize("user_id", [13])
def test_user_nonexistent_values(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND


@mark.parametrize("user_id", [-1, 0, "fafaf"])
def test_user_invalid_values(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
