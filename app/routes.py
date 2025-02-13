from flask import Flask, request, make_response, redirect, render_template, session, flash, g, url_for
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

        
        login_form = LoginForm()

        context = {
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

        return render_template('home.html', **context)

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
                session['user_id'] = user.id
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
        # Verificar si el usuario ha iniciado sesión
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a tu perfil.", "warning")
            return redirect('/login')
        
        # Obtener el usuario actual con sus vehículos
        user = User.query.options(db.joinedload(User.vehiculos)).get(session['user_id'])
        if not user:
            flash("Usuario no encontrado.", "danger")
            return redirect('/login')
        
        # Determinar si estamos en modo edición
        edit_mode = request.args.get('edit') == 'true'
        
        if request.method == 'POST':
            # Validar campos obligatorios
            if not request.form.get('name') or not request.form.get('email'):
                flash("Faltan campos obligatorios.", "error")
                return redirect(url_for('profile'))
            
            # Actualizar datos del usuario
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            user.phone = request.form.get('telefono')
            
            # Guardar cambios en la base de datos
            db.session.commit()
            flash("Perfil actualizado exitosamente.", "success")
            return redirect(url_for('profile'))
        
        # Preparar los datos para enviar a la plantilla
        user_data = user.to_dict()
        return render_template('profile.html', user_data=user_data, edit_mode=edit_mode)


    @app.route('/create_vehicle', methods=['GET', 'POST'])
    def create_vehicle():
        # Verificar si el usuario ha iniciado sesión
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect('/login')
        
        # Obtener el usuario actual
        user = User.query.get(session['user_id'])
        if not user:
            flash("Usuario no encontrado.", "danger")
            return redirect('/login')
        
        if request.method == 'POST':
            # Validar campos obligatorios
            marca = request.form.get('marca')
            modelo = request.form.get('modelo')
            matricula = request.form.get('matricula')
            color = request.form.get('color')
            
            if not marca or not modelo or not matricula or not color:
                flash("Todos los campos son obligatorios.", "error")
                return redirect(url_for('create_vehicle'))
            
            # Validar que la matrícula sea única
            existing_vehicle = Vehiculo.query.filter_by(matricula=matricula).first()
            if existing_vehicle:
                flash("La matrícula ya está registrada.", "error")
                return redirect(url_for('create_vehicle'))
            
            # Crear un nuevo vehículo
            new_vehicle = Vehiculo(
                id_user=user.id,
                marca=marca,
                modelo=modelo,
                matricula=matricula,
                color=color
            )
            db.session.add(new_vehicle)
            db.session.commit()
            
            flash("Vehículo creado exitosamente.", "success")
            return redirect(url_for('profile'))
        
        # Mostrar el formulario de creación
        return render_template('create_vehicle.html')


    @app.route('/edit_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
    def edit_vehicle(vehicle_id):
        # Verificar si el usuario ha iniciado sesión
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect('/login')
        
        # Obtener el vehículo por su ID
        vehicle = Vehiculo.query.get(vehicle_id)
        if not vehicle:
            flash("Vehículo no encontrado.", "danger")
            return redirect(url_for('profile'))
        
        # Verificar que el vehículo pertenece al usuario actual
        if vehicle.id_user != session['user_id']:
            flash("No tienes permiso para editar este vehículo.", "danger")
            return redirect(url_for('profile'))
        
        if request.method == 'POST':
            # Validar campos obligatorios
            marca = request.form.get('marca')
            modelo = request.form.get('modelo')
            matricula = request.form.get('matricula')
            color = request.form.get('color')
            
            if not marca or not modelo or not matricula or not color:
                flash("Todos los campos son obligatorios.", "error")
                return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))
            
            # Validar que la matrícula sea única (excepto para el mismo vehículo)
            existing_vehicle = Vehiculo.query.filter_by(matricula=matricula).first()
            if existing_vehicle and existing_vehicle.id != vehicle.id:
                flash("La matrícula ya está registrada.", "error")
                return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))
            
            # Actualizar los datos del vehículo
            vehicle.marca = marca
            vehicle.modelo = modelo
            vehicle.matricula = matricula
            vehicle.color = color
            
            # Guardar cambios en la base de datos
            db.session.commit()
            
            flash("Vehículo actualizado exitosamente.", "success")
            return redirect(url_for('profile'))
        
        # Mostrar el formulario de edición
        return render_template('edit_vehicle.html', vehicle_data=vehicle.to_dict())


    @app.route('/delete_vehicle/<int:vehicle_id>', methods=['POST'])
    def delete_vehicle(vehicle_id):
        # Verificar si el usuario ha iniciado sesión
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect('/login')
        
        # Obtener el vehículo por su ID
        vehicle = Vehiculo.query.get(vehicle_id)
        if not vehicle:
            flash("Vehículo no encontrado.", "danger")
            return redirect(url_for('profile'))
        
        # Verificar que el vehículo pertenece al usuario actual
        if vehicle.id_user != session['user_id']:
            flash("No tienes permiso para eliminar este vehículo.", "danger")
            return redirect(url_for('profile'))
        
        # Eliminar el vehículo
        db.session.delete(vehicle)
        db.session.commit()
        
        flash("Vehículo eliminado exitosamente.", "success")
        return redirect(url_for('profile'))
        
    # Ruta acceso página información de la empresa
    @app.route('/info')
    def about():
        return render_template('info.html')

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
