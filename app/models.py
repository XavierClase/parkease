from . import db

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