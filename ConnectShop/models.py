from ConnectShop import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True , nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True , nullable=False)
    phone = db.Column(db.String(11), unique=True , nullable=False)

# 임시로 정의한 상품 모델
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    user = db.relationship('User', backref=db.backref('cart_set'))
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 주문 번호 (자동 생성)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    recipient = db.Column(db.String(100), nullable=False)  # 받는 사람
    phone = db.Column(db.String(20), nullable=False)  # 전화번호
    address = db.Column(db.String(200), nullable=False)  # 주소
    total_price = db.Column(db.Integer, nullable=False)  # 총 결제 금액
    payment_method = db.Column(db.String(50), nullable=False)  # 결제 수단
    order_date = db.Column(db.DateTime, default=db.func.now())  # 주문 시간


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False) # 소속 주문서
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False) # 상품 종류
    quantity = db.Column(db.Integer, nullable=False) # 상품 수량
    price = db.Column(db.Integer, nullable=False) # 주문 당시 가격
    order_rel = db.relationship('Order', backref=db.backref('items', cascade='all, delete-orphan'))