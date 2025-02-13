from . import db

# Modelo de usuario
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    dni = db.Column(db.String(9), nullable=False, unique=True)
    phone = db.Column(db.Integer, nullable=False, unique=True)

    # Relación con Vehiculo
    vehiculos = db.relationship('Vehiculo', backref='user', lazy='joined')  # 🔹 Asegura que los vehículos se carguen

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "dni": self.dni,
            "phone": self.phone,
            "vehiculos": [vehiculo.to_dict() for vehiculo in self.vehiculos] # Maneja el caso sin vehículos
        }

    def __repr__(self):
        return f'<User {self.name}>'

# Modelo de Vehículo
class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marca = db.Column(db.String(255))
    modelo = db.Column(db.String(255))
    matricula = db.Column(db.String(255), unique=True)
    color = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "marca": self.marca,
            "modelo": self.modelo,
            "matricula": self.matricula,
            "color": self.color
        }

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(10), unique=True, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ParkingSpot {self.spot_id} - {"Occupied" if self.is_occupied else "Available"}>'

class ParkingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(10), db.ForeignKey('parking_spot.spot_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<ParkingLog {self.spot_id} - {self.user_id} - {self.timestamp}>'

