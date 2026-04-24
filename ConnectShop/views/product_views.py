from flask import Blueprint, render_template, request, abort, g, jsonify, session
from ConnectShop import db
# 🌟 충돌 해결: Coupon과 Review 모델을 둘 다 가져옵니다.
from ConnectShop.models import Product, Coupon, Review
from collections import OrderedDict
from sqlalchemy import func

# 'product'라는 이름의 블루프린트 생성
bp = Blueprint('product', __name__, url_prefix='/product')


@bp.route('/list')
def product_list():
    sel_category = request.args.get('category')
    search_kw = request.args.get('kw', '')  # 🌟 검색어 가져오기

    query = Product.query

    # 1. 검색어가 있는 경우 (이름, 카테고리, 브랜드에서 검색)
    if search_kw:
        search_format = f'%%{search_kw}%%'
        query = query.filter(
            Product.name.ilike(search_format) |
            Product.category.ilike(search_format) |
            Product.brand.ilike(search_format)
        )
        # 검색 시에는 카테고리 필터를 무시하고 전체에서 찾도록 sel_category를 None 처리할 수 있습니다.
        sel_category = f"'{search_kw}' 검색 결과"

    # 2. 검색어는 없고 카테고리만 선택된 경우
    elif sel_category:
        query = query.filter_by(category=sel_category)

    # 최종 결과 조회
    products = query.all()

    # 브랜드별 그룹화 로직 (기존 코드 유지)
    products_by_brand = {}
    for p in products:
        if p.brand not in products_by_brand:
            products_by_brand[p.brand] = []
        products_by_brand[p.brand].append(p)

    return render_template('product/catalog.html',
                           current_category=sel_category,
                           products_by_brand=products_by_brand,
                           search_kw=search_kw)  # 🌟 검색어 전달


# 2. 상세 페이지 함수
@bp.route('/page/<int:product_id>/')
def page(product_id):
    # [1] 데이터베이스에서 해당 상품 정보 가져오기
    product = Product.query.get_or_404(product_id)

    # 🌟 [2] 평균 별점 계산 (여기가 가장 좋은 위치!)
    if product.reviews:
        # 합계를 개수로 나눠 평균 산출
        avg_val = sum(r.rating for r in product.reviews) / len(product.reviews)
        average_rating = round(avg_val, 1)
    else:
        # 리뷰가 아예 없을 때를 대비한 기본값
        average_rating = 0.0

    # [3] 팀장님 로직: 세션에 카테고리 저장
    session['recent_viewed_category'] = product.category

    # [4] 팀원 로직: 옵션 그룹화 (OrderedDict 활용)
    sorted_options = sorted(product.options, key=lambda x: x.id)
    grouped_options = OrderedDict()
    for opt in sorted_options:
        if opt.otype not in grouped_options:
            grouped_options[opt.otype] = []
        grouped_options[opt.otype].append(opt)

    # [5] 추천 상품 로직: 랜덤으로 8개 추출
    recommended_products = Product.query.filter(Product.id != product_id).order_by(func.random()).limit(8).all()

    # [6] 사용자별 맞춤 데이터 (쿠폰, 리뷰 작성 여부)
    coupons = []
    has_reviewed = False
    if g.user:
        coupons = Coupon.query.filter_by(user_id=g.user.id, is_used=False).all()
        existing_review = Review.query.filter_by(user_id=g.user.id, product_id=product_id).first()
        if existing_review:
            has_reviewed = True

    # [7] 마지막: 모든 재료를 템플릿(HTML)으로 전송
    return render_template('product/product_page.html',
                           product=product,
                           grouped_options=grouped_options,
                           coupons=coupons,
                           has_reviewed=has_reviewed,
                           recommended_products=recommended_products,
                           average_rating=average_rating)


# 🌟 팀원분이 추가한 메가 메뉴 동적 데이터 함수 (그대로 유지)
@bp.app_context_processor
def inject_menu_data():
    # 1. 메뉴에 노출하고 싶은 제품의 ID를 사용자님이 원하는 순서대로 적으세요.
    # (예: 각 카테고리별 대표 제품 5개의 ID)
    display_setup = {
        '스마트폰': [1, 13, 21, 29, 37],
        '무선이어폰': [2, 45, 61, 69, 77],
        '스마트워치': [5, 92, 100, 108, 116],
        '태블릿': [124, 132, 140, 148, 156],
        '노트북': [4, 164, 179, 187, 195],
        '헤드폰': [3, 210, 218, 226, 234],
        '블루투스 스피커': [242, 250, 258, 266, 274]
    }

    menu_data = {}
    for cat_name, ids in display_setup.items():
        # 지정한 ID에 해당하는 제품들을 가져오되, 사용자님이 적은 ID 순서대로 정렬해서 가져옵니다.
        products = Product.query.filter(Product.id.in_(ids)).all()
        # 정렬 순서 보장을 위해 다시 한번 정렬 (in_ 쿼리는 순서를 보장하지 않음)
        products.sort(key=lambda p: ids.index(p.id))
        menu_data[cat_name] = products

    return dict(menu_data=menu_data)


# 🌟 [찜하기 기능] 하트를 클릭했을 때 처리하는 로직
@bp.route('/wishlist/<int:product_id>', methods=['POST'])
def toggle_wishlist(product_id):
    # 로그인 안 한 유저가 누르면 거절
    if not g.user:
        return jsonify({'success': False, 'message': 'login_required'}), 401

    from ConnectShop.models import Wishlist

    # 이미 찜한 상품인지 DB에서 확인
    wish = Wishlist.query.filter_by(user_id=g.user.id, product_id=product_id).first()

    if wish:
        # 이미 찜했으면 DB에서 삭제 (빈 하트로 변경 요청)
        db.session.delete(wish)
        db.session.commit()
        return jsonify({'success': True, 'status': 'removed'})
    else:
        # 찜한 적 없으면 DB에 추가 (빨간 하트로 변경 요청)
        new_wish = Wishlist(user_id=g.user.id, product_id=product_id)
        db.session.add(new_wish)
        db.session.commit()
        return jsonify({'success': True, 'status': 'added'})