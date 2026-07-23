from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        """
        데이터베이스 접근을 위해 UserRepository를 받아오는 초기화 메서드
        """
        self.repo = userRepoitory

    def login(self, user_login: UserLogin) -> User:
        """
        사용자 로그인 처리

        Args:
            user_login (UserLogin): 사용자의 이메일과 비밀번호

        Returns:
            User: 로그인이 성공한 사용자

        Raises:
            ValueError: 사용자를 찾을 수 없거나 비밀번호가 일치하지 않는 경우
        """
        user = self.repo.get_user_by_email(user_login.email)
        
        if not user:
            raise ValueError("User not Found.")
        
        if user.password != user_login.password:
            raise ValueError("Invalid ID/PW")
            
        return user
        
    def register_user(self, new_user: User) -> User:
        """
        새로운 사용자 등록

        Args:
            new_user (User): 등록할 사용자

        Returns:
            User: 데이터베이스에 저장된 사용자

        Raises:
            ValueError: 이미 동일한 이메일로 가입된 사용자가 존재하는 경우
        """
        existing_user = self.repo.get_user_by_email(new_user.email)
        
        if existing_user:
            raise ValueError("User already Exists.")
            
        return self.repo.save_user(new_user)

    def delete_user(self, email: str) -> User:
        """
        사용자 삭제

        Args:
            email (str): 삭제할 사용자의 이메일 주소

        Returns:
            User: 삭제가 완료된 사용자 객체

        Raises:
            ValueError: 삭제하려는 이메일의 사용자를 찾을 수 없는 경우
        """
        user = self.repo.get_user_by_email(email)
        
        if not user:
            raise ValueError("User not Found.")
            
        return self.repo.delete_user(user)

    def update_user_pwd(self, user_update: UserUpdate) -> User:
        """
        사용자 비밀번호 변경

        Args:
            user_update (UserUpdate): 변경할 사용자의 이메일과 새로운 비밀번호

        Returns:
            User: 비밀번호가 변경되어 저장된 사용자

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        user = self.repo.get_user_by_email(user_update.email)
        
        if not user:
            raise ValueError("User not Found.")
            
        user.password = user_update.new_password
        self.repo.save_user(user)
        
        return user