from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from paper_digest.users.auth import SESSION_COOKIE, current_user, require_admin
from paper_digest.users.models import User
from paper_digest.users.schemas import (
    CreateUserRequest,
    LoginRequest,
    PasswordRequest,
    UserOut,
)
from paper_digest.users.store import (
    authenticate,
    close_session,
    count_admins,
    create_user,
    delete_user,
    get_user,
    list_users,
    open_session,
    set_password,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


def _out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, is_admin=user.is_admin)


@router.post("/login", response_model=UserOut)
def login(request: LoginRequest, response: Response) -> UserOut:
    user = authenticate(request.email, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong email or password.")
    token, expires_at = open_session(user.id)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        expires=expires_at,
        httponly=True,
        samesite="lax",
    )
    return _out(user)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    if token:
        close_session(token)
    response.delete_cookie(SESSION_COOKIE)


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(current_user)]) -> UserOut:
    return _out(user)


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_admin)])
async def users() -> list[UserOut]:
    return [_out(user) for user in list_users()]


@router.post("", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)])
def add_user(request: CreateUserRequest) -> UserOut:
    try:
        return _out(create_user(request.email, request.password, request.is_admin))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{user_id}/password", status_code=204, dependencies=[Depends(require_admin)])
def change_password(user_id: int, request: PasswordRequest) -> None:
    try:
        set_password(user_id, request.password)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=204)
async def remove_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
) -> None:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    target = get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.is_admin and count_admins() <= 1:
        raise HTTPException(status_code=400, detail="Keep at least one admin.")
    delete_user(user_id)
