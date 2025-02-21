import network
import time
import urequests
from machine import Pin, time_pulse_us

# Definimos los pines para el sensor ultrasónico
TRIGGER_PIN = 12  # Cambiar si es necesario
ECHO_PIN = 13     # Cambiar si es necesario

# Configuración de pines
trigger = Pin(TRIGGER_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

# Conectar a la red Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Alumnes', 'edu71243080')  # Cambia estos valores por tu red Wi-Fi

# Esperar hasta que esté conectada
while not wlan.isconnected():
    print("Conectando...")
    time.sleep(1)

print("Conectada a Wi-Fi con la IP:", wlan.ifconfig()[0])

# Función para medir la distancia
def get_distance():
    # Enviar pulso de disparo
    trigger.off()
    time.sleep_us(2)
    trigger.on()
    time.sleep_us(10)
    trigger.off()

    # Medir la duración del pulso de eco
    try:
        duration = time_pulse_us(echo, 1, 30000)  # Tiempo máximo de espera: 30 ms
    except OSError:
        return None  # Error al medir

    # Calcular la distancia en cm (velocidad del sonido: 34300 cm/s)
    distance = (duration / 2) * 0.0343
    return distance

# Dirección del servidor Flask
url = "http://172.16.1.83:81/sensor"  # Cambiar la ip 
headers = {"Content-Type": "application/json"}

while True:
    # Medir la distancia
    distance = get_distance()
    if distance is not None:
        print("Distancia: {:.2f} cm".format(distance))
        
        # Definir estado basado en la distancia (true si hay un objeto cerca, false si no)
        estado = True if distance < 10 else False
        
        # Formato JSON requerido
        data = {
            "sensorID": "PI",
            "plazaID": 12,
            "estado": estado
        }
        
        try:
            # Enviar solicitud POST con los datos
            response = urequests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                print("Conexión exitosa al servidor Flask")
            else:
                print(f"Error al conectar al servidor Flask, código de estado: {response.status_code}")
            response.close()
        except Exception as e:
            print("Error al conectarse al servidor Flask:", e)
    
    else:
        print("Error en la medición del sensor")

    # Mostrar el estado de la conexión y el valor enviado
    print("Estado enviado:", data)

    time.sleep(60)  # Espera de 1 minuto antes de medir de nuevo

