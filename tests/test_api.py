import math

import requests

from http import HTTPStatus
from pytest import mark
from app.models.User import Users, User, UserUpdate


@mark.usefixtures("fill_test_data")
class TestGetUsers:
    """ GET /api/users/

    Тесты на получение списка пользователей
    """
    def test_users(self, app_url):
        response = requests.get(f'{app_url}/api/users/')
        assert response.status_code == HTTPStatus.OK
        Users.model_validate(response.json())

    def test_get_users_pagination(self, app_url, users):
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
    def test_get_users_all_pagination(self, app_url, users, page_size):
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

    def test_users_no_duplicates(self, users):
        users_ids = [user["id"] for user in users['items']]
        assert len(users_ids) == len(set(users_ids))


class TestGetUser:
    """ GET /api/users/{user_id}

    Тесты на получение пользователя по id
    """

    @mark.parametrize('user_index', [0, -1])
    def test_user(self, app_url, fill_test_data, user_index):
        user_id = fill_test_data[user_index]
        response = requests.get(f'{app_url}/api/users/{user_id}')
        assert response.status_code == HTTPStatus.OK
        user_json = response.json()
        User.model_validate(user_json)

    def test_user_nonexistent_values(self, app_url, fill_test_data):
        user_id = fill_test_data[-1] + 1
        response = requests.get(f"{app_url}/api/users/{user_id}")
        assert response.status_code == HTTPStatus.NOT_FOUND

    @mark.parametrize("user_id", [-1, 0, "text"])
    def test_user_invalid_values(self, app_url, user_id):
        response = requests.get(f"{app_url}/api/users/{user_id}")
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


class TestPostUser:
    """ POST /api/users/

    Тесты на создание пользователя
    """

    def test_post_user(self, app_url, user_data_for_create):
        user_data = user_data_for_create
        response = requests.post(f'{app_url}/api/users',
                                 json=user_data)
        assert response.status_code == HTTPStatus.CREATED
        User.model_validate(response.json())
        user = response.json()
        assert user['email'] == user_data['email']
        assert user['first_name'] == user_data['first_name']
        assert user['last_name'] == user_data['last_name']
        assert user['avatar'] == user_data['avatar']

        response = requests.get(f'{app_url}/api/users/{user["id"]}')
        assert response.status_code == HTTPStatus.OK
        user_get = response.json()
        assert user_get['email'] == user_data['email']
        assert user_get['first_name'] == user_data['first_name']
        assert user_get['last_name'] == user_data['last_name']
        assert user_get['avatar'] == user_data['avatar']

        response_delete = requests.delete(f'{app_url}/api/users/{response.json()["id"]}')
        assert response_delete.status_code == HTTPStatus.OK


class TestPatchUser:
    """ PATCH /api/users/{user_id}

    Тесты на обновление пользователя
    """
    @mark.parametrize('data', [
        UserUpdate(email='updated_mail@test.ru'),
        # UserUpdate(first_name='updated_first_name'),
        # UserUpdate(last_name='updated_last_name'),
        # UserUpdate(avatar='http://updated-uri.ru'),
        # UserUpdate(
        #     email='update_mail@test.ru',
        #     avatar='http://new-avatar.ru',
        #     first_name='new first name'
        # )
    ])
    def test_patch_user(self, app_url, create_user: User, data: UserUpdate):

        json_data = data.model_dump(exclude_unset=True)
        response = requests.patch(
            f'{app_url}/api/users/{create_user.id}',
            json=json_data
        )
        assert response.status_code == HTTPStatus.OK
        assert User.model_validate(response.json())
        user = response.json()
        expect_user_data = create_user.model_dump()
        for k in json_data:
            expect_user_data[k] = json_data[k]

        assert user == expect_user_data, \
            'Данные в ответе не соответсвуют ожидаемым'

        user_get_response = requests.get(f'{app_url}/api/users/{create_user.id}')
        assert user_get_response.status_code == HTTPStatus.OK
        user_get = user_get_response.json()
        assert user_get == expect_user_data, \
            'Данные в БД не соответсвуют ожидаемым'

    def test_patch_user_not_found(self, app_url, fill_test_data):
        user_id = fill_test_data[-1] + 1
        response = requests.patch(
            f'{app_url}/api/users/{user_id}',
            json={'first_name': 'new name'}
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    @mark.parametrize("user_id", [-1, 0, "text"])
    def test_patch_user_invalid_values(self, app_url, user_id):
        response = requests.patch(f"{app_url}/api/users/{user_id}",
                                  json={'first_name': 'new name'})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


class TestDeleteUser:
    """ DELETE /api/users/{user_id}

    Тесты на удаление пользователя
    """

    @mark.parametrize('create_user', [{'delete': False}], indirect=True)
    def test_delete_user(self, app_url, create_user):
        response = requests.delete(f'{app_url}/api/users/{create_user.id}')
        assert response.status_code == HTTPStatus.OK
        response_get = requests.get(f'{app_url}/api/users/{create_user.id}')
        assert response_get.status_code == HTTPStatus.NOT_FOUND

    @mark.parametrize('user_id', [-1, 0, 'text'])
    def test_delete_user_invalid_values(self, app_url, user_id):
        response = requests.get(f'{app_url}/api/users/{user_id}')
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
