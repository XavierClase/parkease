from flask import Flask, request, make_response, redirect, render_template, session, flash, g
from app.forms import LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Vehiculo
from . import db

def register_routes(app):
    # Antes de cada request, definir si hay sesión activa
    @app.before_request
    def before_request():
        g.user_logged_in = 'username' in session

    # Ruta de inicio
    @app.route('/')
    def index():
        user_ip = request.remote_addr
        response = make_response(redirect('/main'))
        session['user_ip'] = user_ip
        return response

    # Ruta principal
    @app.route('/main', methods=['GET', 'POST'])
    def main():
        username = session.get('username')
        if not username:
            return render_template('prelogin.html')

        user_ip = session.get('user_ip')
        login_form = LoginForm()

        context = {
            'ip': user_ip,
            'login_form': login_form,
            'username': username
        }

        if login_form.validate_on_submit():
            username = login_form.username.data
            password = login_form.password.data
            user = User.query.filter_by(username=username).first()

            if user:
                if check_password_hash(user.password, password):
                    session['username'] = username
                    flash("Sesión iniciada correctamente.", "success")
                else:
                    flash("Contraseña incorrecta. Intenta nuevamente.", "error")
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                flash("Usuario creado y sesión iniciada correctamente.", "success")

            return redirect('/main')

        return render_template('information.html', **context)

    # Ruta de inicio de sesión
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            name = request.form.get('username')
            password = request.form.get('password')

            if not name or not password:
                flash("Faltan campos en el formulario.")
                return redirect('/login')

            user = User.query.filter_by(name=name).first()
            if user and check_password_hash(user.password, password):
                session['username'] = name
                flash("Sesión iniciada correctamente.")
                return redirect('/home')
            else:
                flash("Usuario o contraseña incorrectos.")
        return render_template('login.html')

    # Ruta de registro
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            dni = request.form['dni']
            telefono = request.form['telefono']
            marca = request.form.get('marca', None)
            modelo = request.form.get('modelo', None)
            matricula = request.form.get('matricula', None)
            color = request.form.get('color', None)

            hashed_password = generate_password_hash(password)
            new_user = User(name=username, password=hashed_password, email=email, dni=dni, phone=telefono)
            db.session.add(new_user)
            db.session.commit()

            if marca or modelo or matricula or color:
                new_vehiculo = Vehiculo(
                    id_user=new_user.id,
                    marca=marca,
                    modelo=modelo,
                    matricula=matricula,
                    color=color
                )
                db.session.add(new_vehiculo)

            db.session.commit()
            return redirect('/login')

        return render_template('register.html')

    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a tu perfil.", "warning")
            return redirect('/login')

        user_id = session['user_id']
        user = User.query.get(user_id)

        if request.method == 'POST':
            user.username = request.form.get('name')
            user.email = request.form.get('email')
            user.phone = request.form.get('telefono')
            user.modelo_vehiculo = request.form.get('modelo')
            user.matricula = request.form.get('matricula')
            user.color = request.form.get('color')

            db.session.commit()
            flash("Perfil actualizado exitosamente.", "success")

        user_data = user.to_dict()

        return render_template('profile.html', user_data=user_data)

    # Ruta para cerrar sesión
    @app.route('/logout')
    def logout():
        session.clear()
        flash("Sesión cerrada correctamente.")
        return redirect('/')

    # Ruta de sesión activa
    @app.route('/home')
    def home():
        username = session.get('username')
        if username:
            return render_template('home.html', username=username)
        else:
            flash("Por favor inicia sesión primero.")
            return redirect('/login')
