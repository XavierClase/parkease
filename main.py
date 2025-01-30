from flask import Flask, request, make_response, redirect, render_template, session, flash, url_for
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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<User {self.username}>'

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
        username = login_form.username.data
        password = login_form.password.data

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                session['username'] = username
                flash("Sesión iniciada correctamente.")
            else:
                flash("Contraseña incorrecta. Intenta nuevamente.")
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            flash("Usuario creado y sesión iniciada correctamente.")

        return redirect('/main')

    return render_template('information.html', **context)

# Ruta de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash("Sesión iniciada correctamente.")
            return redirect('/main')
        else:
            flash("Usuario o contraseña incorrectos.")
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


# Ruta para página información empresa
@app.route('/info')
def about():
    return render_template('info.html')


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect('/')


# Inicializar base de datos y ejecutar la aplicación
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=81, debug=True)
