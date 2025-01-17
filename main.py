from flask import Flask, request, make_response, redirect, render_template, session, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app
from app.forms import LoginForm

app = create_app()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/python'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<User {self.username}>'



@app.route('/main', methods=['GET', 'POST'])
def main():
    user_ip = request.cookies.get('user_ip')
    if not user_ip:
        user_ip_information = request.remote_addr
        session.clear()
        session['user_ip'] = user_ip_information
        response = make_response(redirect('/main'))
        response.set_cookie('user_ip', user_ip_information, max_age=60*60*24)
        flash("Sesión reiniciada. Por favor, vuelve a intentar.")
        return response
    
    username = session.get('username')

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
                session.clear()
                flash("Contraseña incorrecta. Intenta nuevamente.")
                return redirect('/main')
        else:
            session.clear()
            flash("No se ha encontrado el usuario")

        return redirect('/main')

    return render_template('information.html', **context)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=81, debug=True)
