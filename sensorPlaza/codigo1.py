from machine import Pin, PWM
import time
import urequests
import network

# Configuración de WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Alumnes', 'edu71243080')

while not wlan.isconnected():
    time.sleep(1)
print("Conectado a WiFi")

# Configuración de sensores ultrasónicos para plazas
sensors = [
    {"id": "PS", "plaza": 18, "trigger": 12, "echo": 13},
    {"id": "PI", "plaza": 12, "trigger": 14, "echo": 27}
]

# Configuración del sensor de entrada
trigger_entrada = Pin(26, Pin.OUT)
echo_entrada = Pin(25, Pin.IN)

# Configuración del servo
servo_pin = Pin(33)
servo = PWM(servo_pin, freq=50)

# URLs del servidor
url_plazas = "http://172.16.1.248:81/sensor"
url_entrada = "http://172.16.1.248:81/sensorpuerta"

def medir_distancia(trigger, echo):
    """Mide la distancia usando un sensor ultrasónico."""
    trigger.off()
    time.sleep_us(2)
    trigger.on()
    time.sleep_us(10)
    trigger.off()
    
    tiempo_inicio = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), tiempo_inicio) > 1000000:
            return -1  # Error por timeout
    pulso_inicio = time.ticks_us()
    
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), pulso_inicio) > 1000000:
            return -1  # Error por timeout
    pulso_fin = time.ticks_us()
    
    duracion = time.ticks_diff(pulso_fin, pulso_inicio)
    distancia = (duracion * 0.0343) / 2  # Convertir a cm
    print(f"Distancia medida: {distancia} cm")
    return distancia if distancia > 0 else -1

def enviar_datos(url, data):
    """Envía datos al servidor mediante una solicitud HTTP POST."""
    try:
        respuesta = urequests.post(url, json=data)
        respuesta_json = respuesta.json()
        respuesta.close()
        return respuesta_json
    except Exception as e:
        print("Error al enviar datos:", e)
        return None

def controlar_barrera(estado):
    """Controla el servo de la barrera según la respuesta del servidor."""
    if estado == "detecto":
        servo.duty(40)  # 0°
    else:
        servo.duty(77)  # 90°
    print(f"Barrera {estado}")

def monitorear_plazas():
    """Monitorea las plazas de estacionamiento y envía los datos al servidor."""
    for sensor in sensors:
        trigger = Pin(sensor["trigger"], Pin.OUT)
        echo = Pin(sensor["echo"], Pin.IN)
        distancia = medir_distancia(trigger, echo)
        if distancia == -1:
            continue  # Ignorar lectura inválida
        estado = "ocupado" if distancia < 10 else "libre"
        data_plaza = {"sensorID": sensor["id"], "plazaID": sensor["plaza"], "estado": estado}
        enviar_datos(url_plazas, data_plaza)
        print("Enviado:", data_plaza)

def monitorear_entrada():
    """Monitorea la entrada y controla la barrera según la respuesta del servidor."""
    distancia = medir_distancia(trigger_entrada, echo_entrada)
    if distancia <= 0:
        return  # Ignorar lectura inválida
    estado = "detecto" if distancia < 10 else "no_deteccion"
    data_entrada = {"sensorID": "entrada", "estado": estado}
    respuesta = enviar_datos(url_entrada, data_entrada)
    controlar_barrera(estado)
    

def main():
    while True:
        monitorear_plazas()
        monitorear_entrada()
        time.sleep(15)  # Ajustar según necesidad

if __name__ == "__main__":
    main()

