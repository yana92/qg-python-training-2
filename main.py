import json
from http import HTTPStatus

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi_pagination import Page, paginate, add_pagination

from models.AppStatus import AppStatus
from models.User import User, Users

app = FastAPI()
add_pagination(app)

users: Users = []


@app.get("/status", status_code=HTTPStatus.OK)
def status() -> AppStatus:
    return AppStatus(users=bool(users))


@app.get("/api/users/{user_id}", status_code=HTTPStatus.OK)
def get_user(user_id: int) -> User:
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="Invalid user id")
    if user_id > len(users):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")
    return users[user_id - 1]


@app.get("/api/users/", response_model=Page[User], status_code=HTTPStatus.OK)
def get_users() -> Page[User]:
    return paginate(users)


if __name__ == "__main__":
    with open("users.json") as f:
        users = json.load(f)

    for user in users:
        User.model_validate(user)
    uvicorn.run(app, host="localhost", port=8000)
