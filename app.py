from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffeeshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Automatically generates a unique 8-character ID for each transaction
    customer_id = db.Column(db.String(8), default=lambda: str(uuid.uuid4())[:8], nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product')
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- ROUTES ---
@app.route('/')
def dashboard():
    daily_sales = db.session.query(
        func.date(Sale.date).label('day'), func.sum(Sale.total_price).label('total')
    ).group_by(func.date(Sale.date)).all()
    
    monthly_sales = db.session.query(
        func.strftime('%Y-%m', Sale.date).label('month'), func.sum(Sale.total_price).label('total')
    ).group_by('month').all()
    
    top_products = db.session.query(
        Product.name, func.sum(Sale.quantity).label('qty_sold')
    ).join(Sale).group_by(Product.id).order_by(func.sum(Sale.quantity).desc()).limit(5).all()

    return render_template('dashboard.html', daily=daily_sales, monthly=monthly_sales, top_products=top_products)

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        
        product = Product.query.get(product_id)
        if product:
            sale = Sale(product_id=product.id, quantity=quantity, total_price=product.price * quantity)
            db.session.add(sale)
            db.session.commit()
        return redirect(url_for('sales'))
        
    products = Product.query.all()
    recent_sales = Sale.query.order_by(Sale.date.desc()).limit(15).all()
    return render_template('sales.html', products=products, sales=recent_sales)

# 1. View All Products
@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

# 2. Add New Product
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        db.session.add(Product(name=name, price=price))
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('add_product.html')

# 3. Edit Existing Product
@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['new_price'])
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('edit_product.html', product=product)

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if request.method == 'POST':
        item = request.form['item_name']
        cost = float(request.form['cost'])
        db.session.add(Expense(item_name=item, cost=cost))
        db.session.commit()
        return redirect(url_for('expenses'))
        
    all_expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=all_expenses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)