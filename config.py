import os

# 현재 프로젝트의 최상단 디렉터리 경로를 찾습니다. (teamproject 폴더)
BASE_DIR = os.path.dirname(__file__)

# 데이터베이스 접속 주소: teamproject 폴더 안에 shop.db 라는 이름으로 생성되도록 설정합니다.
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'shop.db'))

# SQLAlchemy의 이벤트를 처리하는 옵션인데, 필요 없으므로 False로 둡니다.
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 폼(WTForms)이나 세션 등을 사용할 때 필요한 비밀키입니다. (실제 서비스에서는 복잡한 문자열로 바꿔야 합니다)
SECRET_KEY = "dev"