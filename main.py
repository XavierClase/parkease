from flask import Flask, request, make_response, redirect, render_template, session, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

from app.forms import LoginForm

# Configuración inicial de Flask y extensiones
app = Flask(
    __name__,
    template_folder=os.path.join('app', 'templates'),  # Configuración para la carpeta de plantillas
    static_folder=os.path.join('app', 'static')       # Configuración para la carpeta estática
)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3308/python'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)

# Modelo de usuario
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    dni = db.Column(db.String(9), nullable=False, unique=True)
    phone = db.Column(db.Integer, nullable=False, unique=True)

    def __repr__(self):
        return f'<User {self.name}>'

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
        return render_template('prelogin.html')  # Mostrar página de pre-login si no hay sesión activa

    user_ip = session.get('user_ip')
    login_form = LoginForm()

    context = {
        'ip': user_ip,
        'login_form': login_form,
        'username': username
    }

    if login_form.validate_on_submit():
        name = login_form.username.data
        password = login_form.password.data

        user = User.query.filter_by(name=name).first()
        if user:
            if check_password_hash(user.password, password):
                session['username'] = name
                flash("Sesión iniciada correctamente.")
            else:
                flash("Contraseña incorrecta. Intenta nuevamente.")
        else:
            flash("Usuario no encontrado. Regístrate primero.")

        return redirect('/main')

    return render_template('information.html', **context)

# Ruta de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')  # Cambiado a 'username'
        password = request.form.get('password')  # No hay cambios aquí

        if not name or not password:
            flash("Faltan campos en el formulario.")
            return redirect('/login')

        user = User.query.filter_by(name=name).first()
        if user and check_password_hash(user.password, password):
            session['username'] = name
            flash("Sesión iniciada correctamente.")
            return redirect('/logeado')
        else:
            flash("Usuario o contraseña incorrectos.")
    return render_template('login.html')



# Modelo de Vehículo
class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'

    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marca = db.Column(db.String(255))
    modelo = db.Column(db.String(255))
    matricula = db.Column(db.String(255), unique=True)
    color = db.Column(db.String(255))

    def __repr__(self):
        return f'<Vehiculo {self.matricula}>'

# Ruta de registro
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # Datos del usuario
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        dni = request.form['dni']
        telefono = request.form['telefono']

        # # Datos del vehículo
        marca = request.form.get('marca', None)
        modelo = request.form.get('modelo', None)
        matricula = request.form.get('matricula', None)
        color = request.form.get('color', None)

        # # Validar que no exista ya el usuario o la matrícula
        # user_exists = User.query.filter((User.email == email) | (User.dni == dni)).first()
        # vehiculo_exists = Vehiculo.query.filter_by(matricula=matricula).first()

        # if user_exists:
        #     flash("El usuario ya existe. Por favor, prueba con otros datos.")
        #     return redirect('/register')

        # if matricula and vehiculo_exists:
        #     flash("La matrícula del vehículo ya está registrada. Intenta con otra.")
        #     return redirect('/register')

        # # Crear usuario
        hashed_password = generate_password_hash(password)
        new_user = User(name=username, password=hashed_password, email=email, dni=dni, phone=telefono)
        db.session.add(new_user)
        db.session.commit()

        # # Crear vehículo (si los datos están presentes)
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
        # flash("Usuario y vehículo registrados correctamente. Ahora puedes iniciar sesión.")
        return redirect('/login')

    return render_template('register.html')


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect('/')

# Ruta de sesión activa
@app.route('/logeado')
def logeado():
    username = session.get('username')
    if username:
        return render_template('logeado.html', username=username)
    else:
        flash("Por favor inicia sesión primero.")
        return redirect('/login')

# Inicializar base de datos y ejecutar la aplicación
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=81, debug=True)