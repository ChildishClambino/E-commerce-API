from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from marshmallow import Schema, fields, validate, ValidationError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Like214!@localhost/e_commerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    accounts = db.relationship('CustomerAccount', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

class CustomerAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    __tablename__ = 'order'  
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    products = db.relationship('OrderProduct', backref='order', cascade="all, delete-orphan")

class OrderProduct(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)  # Update this line
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
# Schemas
class CustomerAccountSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=1))
    password = fields.Str(required=True, validate=validate.Length(min=1))
    customer_id = fields.Int(required=True)

class ProductSchema(Schema):
    product_name = fields.Str(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True)

class OrderProductSchema(Schema):
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)

class OrderSchema(Schema):
    customer_id = fields.Int(required=True)
    products = fields.List(fields.Nested(OrderProductSchema), required=True)


# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Customer Endpoints
@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.json
    try:
        name = data['name']
        email = data['email']
        phone = data['phone']
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e.args[0]}"}), 400

    # Check if the email already exists
    if Customer.query.filter_by(email=email).first():
        return jsonify({"error": "A customer with this email already exists"}), 400

    new_customer = Customer(name=name, email=email, phone=phone)
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "Customer created successfully", "customer_id": new_customer.id}), 201

@app.route('/customers/<int:id>', methods=['GET'])
def read_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        abort(404, description="Customer not found")
    return jsonify({"id": customer.id, "name": customer.name, "email": customer.email, "phone": customer.phone}), 200

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    data = request.json
    customer = Customer.query.get_or_404(id)
    customer.name = data['name']
    customer.email = data['email']
    customer.phone = data['phone']
    db.session.commit()
    return jsonify({"message": "Customer updated successfully"}), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}), 200

@app.route('/customers', methods=['GET'])
def list_customers():
    customers = Customer.query.all()
    customer_list = [{"id": customer.id, "name": customer.name, "email": customer.email, "phone": customer.phone} for customer in customers]
    return jsonify(customer_list), 200

# CustomerAccount Endpoints
@app.route('/customeraccounts', methods=['POST'])
def create_customer_account():
    data = request.json
    schema = CustomerAccountSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    customer_id = validated_data['customer_id']

    # Check if the customer exists
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    new_account = CustomerAccount(**validated_data)
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "Customer account created successfully"}), 201

@app.route('/customeraccounts/<int:id>', methods=['GET'])
def read_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    return jsonify({"id": account.id, "username": account.username, "password": account.password, "customer_id": account.customer_id}), 200

@app.route('/customeraccounts/<int:id>', methods=['PUT'])
def update_customer_account(id):
    data = request.json
    account = CustomerAccount.query.get_or_404(id)
    account.username = data['username']
    account.password = data['password']
    db.session.commit()
    return jsonify({"message": "Customer account updated successfully"}), 200

@app.route('/customeraccounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Customer account deleted successfully"}), 200

# Product Endpoints
@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    schema = ProductSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_product = Product(**validated_data)
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product created successfully"}), 201

@app.route('/products/<int:id>', methods=['GET'])
def read_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({"id": product.id, "product_name": product.product_name, "price": product.price}), 200

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    product = Product.query.get_or_404(id)
    product.product_name = data.get('product_name', product.product_name)
    product.price = data.get('price', product.price)
    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

@app.route('/products', methods=['GET'])
def list_products():
    products = Product.query.all()
    product_list = [{"id": product.id, "product_name": product.product_name, "price": product.price} for product in products]
    return jsonify(product_list), 200

# Order Endpoints
@app.route('/orders', methods=['POST'])
def place_order():
    data = request.json
    schema = OrderSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    customer_id = validated_data['customer_id']
    products = validated_data['products']

    # Check if customer exists
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    new_order = Order(customer_id=customer_id)
    db.session.add(new_order)
    db.session.commit()  # Commit the new order first to get the order ID

    for item in products:
        product_id = item['product_id']
        quantity = item['quantity']

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": f"Product with ID {product_id} not found"}), 404

        order_product = OrderProduct(order_id=new_order.id, product_id=product_id, quantity=quantity)
        db.session.add(order_product)

    db.session.commit()  # Commit the order products

    return jsonify({"message": "Order placed successfully"}), 201

@app.route('/orders/<int:id>', methods=['GET'])
def retrieve_order(id):
    order = Order.query.get_or_404(id)
    order_products = OrderProduct.query.filter_by(order_id=id).all()
    products = [{"product_id": op.product_id, "quantity": op.quantity} for op in order_products]
    return jsonify({"id": order.id, "order_date": order.order_date, "customer_id": order.customer_id, "products": products}), 200

@app.route('/orders/<int:id>/track', methods=['GET'])
def track_order(id):
    order = Order.query.get_or_404(id)
    return jsonify({"id": order.id, "order_date": order.order_date, "customer_id": order.customer_id}), 200

@app.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    data = request.json
    order = Order.query.get_or_404(id)
    order.order_date = data['order_date']
    order.customer_id = data['customer_id']
    db.session.commit()

    # Remove existing order products
    OrderProduct.query.filter_by(order_id=id).delete()

    # Add updated order products
    for item in data['products']:
        product_id = item['product_id']
        quantity = item['quantity']

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": f"Product with ID {product_id} not found"}), 404

        order_product = OrderProduct(order_id=id, product_id=product_id, quantity=quantity)
        db.session.add(order_product)

    db.session.commit()
    return jsonify({"message": "Order updated successfully"}), 200

@app.route('/orders/<int:id>', methods=['DELETE'])
def cancel_order(id):
    order = Order.query.get_or_404(id)
    # Delete related order products
    OrderProduct.query.filter_by(order_id=id).delete()
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Order cancelled successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)