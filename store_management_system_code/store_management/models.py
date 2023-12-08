from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Float
from sqlalchemy import DateTime

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "productcategory"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    categoryId = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable=False)


class ProductOrder(database.Model):
    __tablename__ = "productorder"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable=False)
    quantity = database.Column(database.Integer, nullable=False)


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key=True)
    productName = database.Column(database.String(256), nullable=False, unique=True)
    productPrice = database.Column(Float, nullable=False)

    categories = database.relationship("Category", secondary=ProductCategory.__table__, back_populates="products")
    orders = database.relationship("Order", secondary=ProductOrder.__table__, back_populates="products")


class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key=True)
    categoryName = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories")


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key=True)
    totalOrderPrice = database.Column(Float, nullable=False)
    orderStatus = database.Column(database.String(256), nullable=False)
    orderCreationTime = database.Column(DateTime, nullable=False)
    buyerEmail = database.Column(database.String(256), nullable=False)

    products = database.relationship("Product", secondary=ProductOrder.__table__, back_populates="orders")
