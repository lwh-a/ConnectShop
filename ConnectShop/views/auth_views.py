from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from ConnectShop import db
from ConnectShop.forms import UserCreateForm, UserLoginForm, FindIdForm, ResetPasswordForm
from ConnectShop.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


# 1. 회원가입
@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = UserCreateForm()
    if request.method == 'POST' and form.validate_on_submit():
        # 중복 검사: 이메일과 이름(username) 기준
        user_email = User.query.filter_by(email=form.email.data).first()
        user_name = User.query.filter_by(username=form.username.data).first()

        if not user_email and not user_name:
            user = User(
                email=form.email.data,
                password=generate_password_hash(form.password1.data),  # 암호화 저장
                username=form.username.data,
                phone=form.phone.data
            )
            db.session.add(user)
            db.session.commit()
            flash('회원가입이 완료되었습니다. 로그인 해주세요.')
            return redirect(url_for('auth.login'))
        elif user_name:
            flash('이미 존재하는 이름입니다.')
        else:
            flash('이미 존재하는 이메일입니다.')

    return render_template('auth/signup.html', form=form)



@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = UserLoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            error = "등록되지 않은 이메일입니다."
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 맞지 않습니다."
        else:

            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('main.index'))

        flash(error)

    return render_template('auth/login.html', form=form)



# 3. 로그아웃
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))


# 4. 아이디(이메일) 찾기
@bp.route('/find_id', methods=['GET', 'POST'])
def find_id():
    # 파인드인포html에서 사용하는 두 가지 폼을 모두 전달
    find_id_form = FindIdForm()
    reset_pw_form = ResetPasswordForm()

    if request.method == 'POST' and find_id_form.validate_on_submit():
        user = User.query.filter_by(username=find_id_form.username.data).first()
        if user:
            flash(f"찾으시는 이메일은 {user.email} 입니다.")
        else:
            flash("가입된 정보가 없습니다.")

    return render_template('auth/find_info.html',
                           find_id_form=find_id_form,
                           reset_pw_form=reset_pw_form)


# 5. 비밀번호 재설정
@bp.route('/find_password', methods=['GET', 'POST'])
def find_password():
    find_id_form = FindIdForm()
    reset_pw_form = ResetPasswordForm()

    if request.method == 'POST' and reset_pw_form.validate_on_submit():
        # 이름과 이메일이 동시에 일치하는지 확인 [cite: 1, 10]
        user = User.query.filter_by(username=reset_pw_form.username.data,
                                    email=reset_pw_form.email.data).first()
        if user:
            user.password = generate_password_hash(reset_pw_form.password1.data)
            db.session.commit()
            flash("비밀번호가 성공적으로 변경되었습니다.")
            return redirect(url_for('auth.login'))
        else:
            flash("입력하신 정보와 일치하는 사용자가 없습니다.")

    return render_template('auth/find_info.html',
                           find_id_form=find_id_form,
                           reset_pw_form=reset_pw_form)


# 로그인 상태 확인 (g 객체 활용)
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

#구글 로그인
#
# @app.route('/auth/google')
# def google_login():
#     redirect_uri = url_for('google_callback', _external=True)
#     return oauth.google.authorize_redirect(redirect_uri)
#
#
# @app.route('/auth/google/callback')
# def google_callback():
#     token = oauth.google.authorize_access_token()
#     user = token['userinfo']
#
#     email = user['email']
#     name = user['name']
#
#     # 👉 여기서 DB 조회 / 회원 생성 / 로그인 처리
#     return redirect(url_for('main.index'))
