from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow import ValidationError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Like214!@localhost/e_comerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)


class CustomerSchema(ma.Schema):
    name=  fields.String(required=True)
    email= fields.String(required=True)
    phone= fields.String(required=True)


    class Meta:
        fields=("name","email","phone","id")


customer_schema=CustomerSchema()
customers_schema=CustomerSchema(many=True)


class Customer(db.Model):
    __tablename__= 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email =db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders = db.relationship('Order', backref='customer')  # establishing realationship


order_product = db.Table("Order_Product",
    db.Column("order_id", db.Integer, db.ForeignKey("Orders.id"), primary_key=True),
    db.Column("product_id", db.Integer, db.ForeignKey("Products.id"), primary_key=True)
)


class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    product_name = db.Column(db.String, nullable=False)
    products = db.relationship('Product', secondary=order_product, backref='order_items')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'date': self.date,
            'product_name' : db.Column(db.String, nullable=False) 
        }
    # One-To-One


class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer,  primary_key= True)
    username= db.Column(db.String(255), unique =True, nullable=False)
    password= db.Column(db.String(255), nullable= False)
    customer_id= db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref= 'customer_account', uselist=False)



class Product(db.Model):
    __tablename__='Products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)


@app.route('/customers', methods=['GET'])   # get all customers
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)


@app.route('/customeraccounts/<int:customer_id>', methods=['GET'])  # get a customer account
def get_customer_account(customer_id):
    customer_account = CustomerAccount.query.filter_by(customer_id=customer_id).first_or_404()
    return jsonify({"username": customer_account.username}), 200


@app.route('/customers', methods=['POST'])     # add a new customer
def add_customer():
    try:       
        customer_data= customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], phone=customer_data['phone'])    # create a new customer
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "New customer added successfully"}), 201


@app.route('/customeraccounts', methods=['POST'])   # add a new customer account
def add_customer_account():
    try:
        customer_account_data = request.json
        customer_account = CustomerAccount(username=customer_account_data['username'], password=customer_account_data['password'], customer_id=customer_account_data['customer_id'])
        db.session.add(customer_account)
        db.session.commit()
        return jsonify({"message": "New customer account added successfully"}), 201
    except Exception as e:
        return jsonify({"message": "An error occurred"}), 500


@app.route('/customers/<int:id>', methods=['PUT'])    # update a customer
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data =customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    

    customer.name =customer_data['name']
    customer.email =customer_data['email']
    customer.phone =customer_data['phone']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200


@app.route('/customeraccounts/<int:id>', methods=['PUT'])       # update a customer account
def update_customer_account(id):
    customer_account = CustomerAccount.query.get_or_404(id)
    customer_account_data = request.json
    customer_account.username = customer_account_data['username']
    customer_account.password = customer_account_data['password']
    customer_account.customer_id = customer_account_data['customer_id']
    db.session.commit()
    return jsonify({"message": "Customer account details updated successfully"}), 200


@app.route('/customers/<int:id>', methods=['DELETE'])   # delete a customer
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200


@app.route('/customeraccounts/<int:id>', methods=['DELETE'])    # delete a customer account
def delete_customer_account(id):
    customer_account = CustomerAccount.query.get_or_404(id)
    db.session.delete(customer_account)
    db.session.commit()
    return jsonify({"message": "Customer account removed successfully"}), 200


@app.route('/products', methods=['GET'])   # get all products
def get_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_data = {
            'id': product.id,
            'product_name': product.product_name,
            'price': product.price,
        }
        product_list.append(product_data)
    return jsonify(product_list), 200


@app.route('/products', methods=['POST'])    # add a new product
def add_product():
    product_data = request.json
    product = Product(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "New product added successfully"}), 201


@app.route('/products/<int:id>', methods=['PUT'])   # update a product
def update_product(id):
    product = Product.query.get_or_404(id)
    product_data = request.json
    product.name = product_data['product_name']
    product.price = product_data['price']
    db.session.commit()
    return jsonify({"message": "Product details updated successfully"}), 200


@app.route('/products/<int:id>', methods=['DELETE'])  # delete a product
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product removed successfully"}), 200


@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    order_list = [
        {column.name: getattr(order, column.name) for column in order.__table__.columns}
        for order in orders
    ]
    
    return jsonify(order_list), 200


@app.route('/orders', methods=['POST'])     # add a new order
def add_order():
    order_data = request.json
    customer_id = order_data['customer_id']

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404


    order = Order(date=order_data['date'], customer_id=customer_id, product_name=order_data['product_name'])
    db.session.add(order)
    db.session.commit()
    return jsonify({"message": "New order added successfully"}), 201


@app.route('/orders/<int:id>', methods=['PUT'])   # update an order
def update_order(id):
    order = Order.query.get_or_404(id)
    order_data = request.json
    order.date = order_data['date']
    order.customer_id = order_data['customer_id']
    db.session.commit()
    return jsonify({"message": "Order details updated successfully"}), 200


@app.route('/orders/<int:id>', methods=['DELETE'])    # delete an order
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Order removed successfully"}), 200


if __name__=='__main__':
    app.run(debug=True)