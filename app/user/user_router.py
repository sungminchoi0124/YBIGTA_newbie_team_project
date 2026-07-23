from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    ## TODO
    """
    신규 사용자 등록 처리

    service.register_user(user)에 위임하여 이메일 중복 체크와 사용자 저장을 수행하고,
    결과를 BaseResponse로 감싸 return.

    Args:
        user (User): 등록할 사용자 정보 (email, password, username)

    Returns:
        BaseResponse[User]: 등록된 사용자 정보를 담은 성공 응답

    Raises:
        HTTPException: 이미 동일한 이메일로 가입된 사용자가 있는 경우 (400 Bad Request)
    """
    try:
        new_user = service.register_user(user)
        return BaseResponse(status="success", data=new_user, message="Register Success.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    ## TODO
    """
    사용자 삭제 처리

    요청 body에서 삭제할 사용자의 이메일을 꺼내 service.delete_user(email)에 위임하고,
    결과를 BaseResponse로 감싸 return.

    Args:
        user_delete_request (UserDeleteRequest): 삭제할 사용자의 이메일을 담은 요청

    Returns:
        BaseResponse[User]: 삭제된 사용자 정보를 담은 성공 응답

    Raises:
        HTTPException: 해당 이메일의 사용자를 찾을 수 없는 경우 (404 Not Found)
    """
    try:
        deleted_user = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=deleted_user, message="Delete Success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    ## TODO
    """
    사용자 비밀번호 변경 처리

    이메일과 새 비밀번호가 담긴 요청을 service.update_user_pwd(user_update)에 위임하여
    기존 사용자 조회 및 비밀번호 갱신을 수행하고, 결과를 BaseResponse로 감싸 return.

    Args:
        user_update (UserUpdate): 변경할 사용자의 이메일과 새로운 비밀번호

    Returns:
        BaseResponse[User]: 비밀번호가 변경된 사용자 정보를 담은 성공 응답

    Raises:
        HTTPException: 해당 이메일의 사용자를 찾을 수 없는 경우 (404 Not Found)
    """
    try:
        updated_user = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=updated_user, message="Password Update Success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
