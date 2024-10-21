from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(500))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    marker = db.Column(db.String(50))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    notes = db.relationship('Note')
    financeiro = db.relationship('Financeiro', backref='user', uselist=False)
    documentos = db.relationship('Documento', backref='user', lazy=True)

class Financeiro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    objetivo_gastos = db.Column(db.Float, default=100.00)
    categoria = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    moeda = db.Column(db.String(10))
    
    usuario = db.relationship('User', backref='financeiros') 

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(db.DateTime(timezone=True), default=func.now())