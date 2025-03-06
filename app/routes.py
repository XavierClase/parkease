from flask import Flask, request, make_response, redirect, render_template, session, g, flash, jsonify, url_for
from app.forms import LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Vehiculo, ParkingInferior, ParkingSuperior, ParkingLog
from . import db
from datetime import datetime, timedelta
# from django.utils import timezone

sensor_status = {}

def register_routes(app):
    # Antes de cada request, definir si hay sesión activa
    @app.before_request
    def before_request():
        g.user_logged_in = 'username' in session


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
            
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username

            return redirect('/main')

        return render_template('home.html', **context)

    # Ruta de inicio de sesión
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            name = request.form.get('username')
            password = request.form.get('password')

            if not name or not password:
                return redirect('/login')

            user = User.query.filter_by(name=name).first()
            if user and check_password_hash(user.password, password):
                session['username'] = name
                session['user_id'] = user.id
                return redirect('/home')
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
    
    # Ruta Parking Inferior
    @app.route('/parkinginferior', methods=["GET", "POST"])
    def parkinf():

        plazas_data = ParkingInferior.query.all()

        if request.method == 'POST':
            numero_plaza = request.form.get('numero')
            parking_inferior = ParkingInferior.query.filter_by(numero=numero_plaza).first()

            if parking_inferior:
                ParkingInferior.ocupada = int(request.form.get('ocupada'))  
                db.session.commit()

            plazas_data = parking_inferior.query.all()
                
        return render_template('parkinf.html', plazas=plazas_data)

        
    
    # Ruta Parking Superior
    @app.route('/parkingsuperior', methods=["GET", "POST"])
    def parksup():

        plazas_data = ParkingSuperior.query.all()

        if request.method == 'POST':
            numero_plaza = request.form.get('numero')
            parking_superior = ParkingSuperior.query.filter_by(numero=numero_plaza).first()

            if parking_superior:
                ParkingSuperior.ocupada = int(request.form.get('ocupada')) 
                db.session.commit()

            # Volvemos a obtener todas las plazas después de actualizar
            plazas_data = parking_superior.query.all()
                
        return render_template('parksup.html', plazassup=plazas_data)


    @app.route('/api/entrada', methods=['POST'])
    def entrada():
        data = request.get_json(force=True)
        matricula = data.get('matricula')
        
        reg = Vehiculo.query.filter_by(matricula=matricula).first()

        if not reg:
            return jsonify({'error': 'Matrícula no registrada'}), 403
        
        spot_libre_inf = ParkingInferior.query.filter_by(ocupada=False).first()
        spot_libre_sup = ParkingSuperior.query.filter_by(ocupada=False).first()

        if spot_libre_inf:
            new_log = ParkingLog(
                matricula=matricula,
                tiempo_entrada=datetime.now(),
                tiempo_salida=None
            )
            db.session.add(new_log)
            spot_libre_inf.ocupada = True  
            db.session.commit()
            return jsonify({'success': 'Entrada registrada'}), 200

        elif spot_libre_sup:
            new_log = ParkingLog(
                matricula=matricula,
                tiempo_entrada=datetime.now(),
                tiempo_salida=None
            )
            db.session.add(new_log)
            spot_libre_sup.ocupada = True  
            db.session.commit()
            return jsonify({'success': 'Entrada registrada en parking superior'}), 200

        return jsonify({'error': 'Parking completo'}), 409


    @app.route('/api/actualizarplaza', methods=['POST'])
    def actualizarplaza():
        data = request.get_json(force=True)
        
        sensor_id = data.get('sensorID')  
        plaza_id = data.get('plazaID')
        estado = data.get('estado')  
        
        if sensor_id not in ['PS', 'PI']:
            return jsonify({'error': 'ID de sensor inválido'}), 400

        if sensor_id == 'PS':
            plaza = ParkingSuperior.query.filter_by(numero=plaza_id).first()
        else:  # sensor_id == 'PI'
            plaza = ParkingInferior.query.filter_by(numero=plaza_id).first()

        if not plaza:
            return jsonify({'error': 'Plaza no encontrada'}), 404

        plaza.ocupada = bool(estado)
        db.session.commit()

        return jsonify({'success': 'Plaza actualizada'}), 200



    @app.route('/api/salida', methods=['POST'])
    def salida():
        data = request.get_json(force=True)
        matricula = data.get('matricula')

        reg = Vehiculo.query.filter_by(matricula=matricula).first()

        if not reg:
            return jsonify({'error': 'Matricula no registrada'}), 403
        
        log = ParkingLog.query.filter_by(matricula=matricula, tiempo_salida=None).first()

        if not log:
            return jsonify({'error': 'No hay registro de entrada para esta matrícula'}), 404

        log.tiempo_salida = datetime.now()

        # Liberar la plaza ocupada por el vehículo
        plaza_inf = ParkingInferior.query.filter_by(ocupada=True).first()
        plaza_sup = ParkingSuperior.query.filter_by(ocupada=True).first()

        if plaza_inf:
            plaza_inf.ocupada = False
        elif plaza_sup:
            plaza_sup.ocupada = False

        db.session.commit()
        return jsonify({'success': 'Salida registrada'}), 200


    @app.route('/parking_log', methods=['POST'])
    def verificar_cambio():
        try:
            # Definir el tiempo de verificación (últimos 60 segundos)
            ahora = datetime.utcnow()
            tiempo_limite = ahora - timedelta(seconds=60)

            # Verificar si hay cambios recientes en tiempo_entrada o tiempo_salida
            cambios = ParkingLog.query.filter(
                (ParkingLog.tiempo_entrada >= tiempo_limite) | 
                (ParkingLog.tiempo_salida >= tiempo_limite)
            ).first()

            if cambios:
                print("⚡ Se detectó un cambio en la tabla parking_log.")
                return jsonify({"cambio": True}), 200
            else:
                print("🔸 No hay cambios recientes en la tabla parking_log.")
                return jsonify({"cambio": False}), 200
        except Exception as e:
            print(f"❌ Error al verificar cambios en la base de datos: {e}")
            return jsonify({"error": "Error en la base de datos"}), 500

    @app.route('/sensorpuerta', methods=['POST'])
    def recibir_datos_sensor():
        try:
            data = request.json
            sensor_id = data.get("sensorID")
            estado = data.get("estado")

            if sensor_id is not None and estado is not None:
                print(f"📡 Sensor {sensor_id} ha detectado un objeto cerca: {estado}")
                return jsonify({"mensaje": "Datos recibidos correctamente"}), 200
            else:
                return jsonify({"error": "Datos inválidos"}), 400
        except Exception as e:
            print(f"❌ Error procesando datos del sensor: {e}")
            return jsonify({"error": "Error interno"}), 500

    @app.route('/sensor', methods=['POST'])
    def receive_sensor_data():
        global sensor_status
        data = request.get_json()
    
        if data and "sensorID" in data and "plazaID" in data and "estado" in data:
            try:
                sensorID = data["sensorID"]
                plazaID = int(data["plazaID"])
                estado = bool(data["estado"])  # Convertir a booleano

                sensor_status = {
                    "sensorID": sensorID,
                    "plazaID": plazaID,
                    "estado": estado
                }

                print("Datos recibidos:", sensor_status)

                # Hacer una petición interna a '/api/actualizarplaza'
                with app.test_request_context('/api/actualizarplaza', method='POST', json=sensor_status):
                    return actualizarplaza()

            except ValueError:
                return jsonify({"error": "Formato de datos inválido"}), 400
        else:
            return jsonify({"error": "Datos inválidos"}), 400

    # Ruta de inicio
    @app.route('/')
    def index():
        user_ip = request.remote_addr
        response = make_response(redirect('/main'))
        session['user_ip'] = user_ip
        return response


    # Ruta para cerrar sesión
    @app.route('/logout')
    def logout():
        session.clear()
<<<<<<< HEAD
        flash("Sesión cerrada correctamente.")
        return redirect('/login')
=======
        return redirect('/')
>>>>>>> origin/alex

    # Ruta de sesión activa
    @app.route('/home')
    def home():
        username = session.get('username')
        if username:
            return render_template('home.html', username=username)
        else:
            flash("Por favor inicia sesión primero.")
            return redirect('/login')


