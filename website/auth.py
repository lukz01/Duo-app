from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Voce esta logado!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Senha esta errada, tente novamente.', category='error')
        else:
            flash('Email nao existe!', category='error')


    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        nome = request.form.get('nome')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email ja registrado!', category='error')
        elif len(email) < 4:
            flash('Email deve conter mais que 3 caracteres', category="error")
        elif len(nome) < 2:
            flash('Nome deve conter pelo menos 2 caracteres', category="error")
        elif password1 != password2:
            flash('Senhas nao correspondem!', category="error")
        elif len(password1) < 7:
            flash('Senha deve conter pelo menos 7 caracteres', category="error")
        else:
            new_user = User(email=email, name=nome, password=generate_password_hash(password1, method="pbkdf2:sha256"))
            db.session.add(new_user)
            db.session.commit()
            login_user(user, remember=True)

            flash("Conta criada!", category="success")

            return redirect(url_for('views.home'))

    return render_template("signup.html", user=current_user)