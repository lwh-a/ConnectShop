from types import SimpleNamespace
from flask import Blueprint, render_template, redirect, url_for, session, g, flash, jsonify, request

from ConnectShop import db
from ConnectShop.models import Cart, Product, Order, OrderItem

bp = Blueprint('order', __name__, url_prefix='/order')


# --- Helper Functions ---
def get_guest_cart():
    return session.get('guest_cart', [])


def save_guest_cart(cart):
    session['guest_cart'] = cart
    session.modified = True


def get_cart_items():
    if g.user:
        return Cart.query.filter_by(user_id=g.user.id).all()

    guest_cart = get_guest_cart()
    cart_list = []
    for item in guest_cart:
        product = db.session.get(Product, item['product_id'])
        if product:
            cart_list.append(SimpleNamespace(product=product, quantity=item['quantity'], product_id=product.id))
    return cart_list


# --- Routes ---
@bp.route('/list')
def _list():
    cart_list = get_cart_items()
    total_price = sum(item.product.price * item.quantity for item in cart_list)
    return render_template('order/cart_list.html', cart_list=cart_list, total_price=total_price)


@bp.route('/add/<int:product_id>')
def add(product_id):
    if g.user:
        cart = Cart.query.filter_by(user_id=g.user.id, product_id=product_id).first()
        if cart:
            cart.quantity += 1
        else:
            db.session.add(Cart(user_id=g.user.id, product_id=product_id, quantity=1))
        db.session.commit()
    else:
        guest_cart = get_guest_cart()
        item = next((i for i in guest_cart if i['product_id'] == product_id), None)
        if item:
            item['quantity'] += 1
        else:
            guest_cart.append({'product_id': product_id, 'quantity': 1})
        save_guest_cart(guest_cart)
    return redirect(url_for('order._list'))


# @ 기호가 빠졌던 부분을 수정했습니다.
@bp.route('/modify/<int:product_id>/<string:action>', methods=['POST'])
def modify(product_id, action):
    new_quantity = 1
    unit_price = 0

    if g.user:
        cart_item = Cart.query.filter_by(user_id=g.user.id, product_id=product_id).first()
        if cart_item:
            if action == 'inc':
                cart_item.quantity += 1
            elif action == 'dec' and cart_item.quantity > 1:
                cart_item.quantity -= 1
            db.session.commit()
            new_quantity = cart_item.quantity
            unit_price = cart_item.product.price
    else:
        guest_cart = get_guest_cart()
        for item in guest_cart:
            if item['product_id'] == product_id:
                if action == 'inc':
                    item['quantity'] += 1
                elif action == 'dec' and item['quantity'] > 1:
                    item['quantity'] -= 1
                new_quantity = item['quantity']
                product = db.session.get(Product, product_id)
                unit_price = product.price if product else 0
                break
        save_guest_cart(guest_cart)

    cart_list = get_cart_items()
    total_price = sum(item.product.price * item.quantity for item in cart_list)

    return jsonify({
        'success': True,
        'new_quantity': new_quantity,
        'item_total': format(unit_price * new_quantity, ','),
        'total_price': format(total_price, ',')
    })


@bp.route('/delete/<int:product_id>')
def delete(product_id):
    if g.user:
        cart_item = Cart.query.filter_by(user_id=g.user.id, product_id=product_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
    else:
        guest_cart = [i for i in get_guest_cart() if i['product_id'] != product_id]
        save_guest_cart(guest_cart)
    return redirect(url_for('order._list'))

@bp.route('/checkout')
def checkout():
    cart_list = get_cart_items()

    if not cart_list:
        flash("장바구니가 비어 있습니다.")
        return redirect(url_for('order._list'))

    total_price = sum(item.product.price * item.quantity for item in cart_list)

    return render_template('order/checkout.html', cart_list=cart_list, total_price=total_price)


@bp.route('/place_order', methods=['POST'])
def place_order():
    recipient = request.form.get('recipient')
    phone = request.form.get('phone')[:13]
    address = f"{request.form.get('address')} {request.form.get('address_detail')}"
    payment_method = request.form.get('payment_method')

    cart_list = get_cart_items()
    if not cart_list:
        flash("장바구니가 비어 있습니다.")
        return redirect(url_for('main.index'))

    total_price = sum(item.product.price * item.quantity for item in cart_list)

    new_order = Order(
        user_id=g.user.id if g.user else None,
        recipient=recipient,
        phone=phone,
        address=address,
        total_price=total_price,
        payment_method=payment_method
    )
    db.session.add(new_order)

    for item in cart_list:
        order_item = OrderItem(
            order_rel=new_order,  # 위에서 만든 주문서와 연결
            product_id=item.product.id,
            quantity=item.quantity,
            price=item.product.price  # 주문 시점의 가격 기록
        )
        db.session.add(order_item)

    if g.user:
        Cart.query.filter_by(user_id=g.user.id).delete()
    else:
        session.pop('guest_cart', None)

    db.session.commit()

    flash("주문이 성공적으로 완료되었습니다!")
    return render_template('order/order_complete.html', order=new_order)