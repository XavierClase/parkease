from flask import Flask, request, make_response, redirect, render_template, session, flash, url_for
from app.forms import LoginForm 
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db

def register_routes(app):
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
        # Verificar si el usuario ya tiene una sesión activa
        username = session.get('username')
        if not username:
            # Si no hay sesión activa, mostrar la página de pre-login
            return render_template('prelogin.html')

        # Obtener la dirección IP del usuario desde la sesión
        user_ip = session.get('user_ip')

        # Inicializar el formulario de inicio de sesión
        login_form = LoginForm()

        # Preparar contexto para pasar al template
        context = {
            'ip': user_ip,
            'login_form': login_form,
            'username': username
        }

        # Manejar el envío del formulario
        if login_form.validate_on_submit():
            username = login_form.username.data
            password = login_form.password.data

            # Buscar al usuario en la base de datos
            user = User.query.filter_by(username=username).first()

            if user:
                # Verificar la contraseña del usuario existente
                if check_password_hash(user.password, password):
                    session['username'] = username
                    flash("Sesión iniciada correctamente.", "success")
                else:
                    flash("Contraseña incorrecta. Intenta nuevamente.", "error")
            else:
                # Crear un nuevo usuario si no existe
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                flash("Usuario creado y sesión iniciada correctamente.", "success")

            return redirect('/main')

        # Renderizar la página principal con el contexto actualizado
        return render_template('information.html', **context)


    # Ruta de inicio de sesión
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Recuperar datos del formulario
            username = request.form['username']
            password = request.form['password']
            
            # Buscar el usuario en la base de datos
            user = User.query.filter_by(username=username).first()
            
            # Verificar credenciales
            if user and check_password_hash(user.password, password):
                # Guardar datos del usuario en la sesión
                session['user_id'] = user.id
                session['username'] = user.username
                session['email'] = user.email
                session['name'] = user.name
                session['surname'] = user.surname
                
                return redirect('/profile')
            else:
                return redirect('/login')
        return render_template('login.html')

    # Ruta de registro
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user:
                flash("El usuario ya existe. Prueba con otro nombre.")
                return redirect('/register')

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Usuario registrado correctamente. Ahora puedes iniciar sesión.")
            return redirect('/login')
        return render_template('register.html')


    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        # Verificar si el usuario está autenticado
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a tu perfil.", "warning")
            return redirect('/login')

        # Recuperar los datos del usuario autenticado
        user_id = session['user_id']
        user = User.query.get(user_id)

        if request.method == 'POST':
            # Si se envían datos para actualizar el perfil, procesarlos
            user.name = request.form.get('name')
            user.surname = request.form.get('surname')
            user.email = request.form.get('email')
            user.telefono = request.form.get('telefono')
            user.modelo_vehiculo = request.form.get('modelo')
            user.matricula = request.form.get('matricula')
            user.color = request.form.get('color')

            # Guardar los cambios en la base de datos
            db.session.commit()
            flash("Perfil actualizado exitosamente.", "success")

        # Preparar los datos del usuario para el template
        user_data = user.to_dict()

        return render_template('profile.html', user_data=user_data)

    # Ruta para cerrar sesión
    @app.route('/logout')
    def logout():
        session.clear()
        flash("Sesión cerrada correctamente.")
        return redirect('/')