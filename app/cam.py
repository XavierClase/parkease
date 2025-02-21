# OpenCV libs
import cv2
import numpy as np
# Configura la ruta de Tesseract si es necesario (solo en Windows)
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Extra Libs
import requests  # HTTP camera acquisition
import time  # time.sleep

# recojemos la IP de la camara (1er parametro) y generamos la URL para capturar frames
esp32_url = "http://172.16.5.66/capture"

def ordenar_puntos(puntos):
    # Ordenar los puntos en el orden: top-left, top-right, bottom-right, bottom-left
    puntos = puntos.reshape(4, 2)  # Asegúrate de que tenga forma (4, 2)
    suma = puntos.sum(axis=1)
    diferencia = np.diff(puntos, axis=1)
    top_left = puntos[np.argmin(suma)]
    bottom_right = puntos[np.argmax(suma)]
    top_right = puntos[np.argmin(diferencia)]
    bottom_left = puntos[np.argmax(diferencia)]
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")

def enderezar_imagen(imagen, puntos):
    # Ordenar los puntos detectados
    puntos_ordenados = ordenar_puntos(puntos)
    # Calcular el ancho y alto de la nueva imagen
    (top_left, top_right, bottom_right, bottom_left) = puntos_ordenados
    ancho1 = np.linalg.norm(bottom_right - bottom_left)
    ancho2 = np.linalg.norm(top_right - top_left)
    max_ancho = max(int(ancho1), int(ancho2))
    alto1 = np.linalg.norm(top_right - bottom_right)
    alto2 = np.linalg.norm(top_left - bottom_left)
    max_alto = max(int(alto1), int(alto2))
    # Puntos de destino para la transformación
    destino = np.array([
        [0, 0],
        [max_ancho - 1, 0],
        [max_ancho - 1, max_alto - 1],
        [0, max_alto - 1]
    ], dtype="float32")
    # Calcular la matriz de transformación de perspectiva
    matriz = cv2.getPerspectiveTransform(puntos_ordenados, destino)
    # Aplicar la transformación de perspectiva
    imagen_enderezada = cv2.warpPerspective(imagen, matriz, (max_ancho, max_alto))
    return imagen_enderezada

# Loop principal (se sale con tecla Q)
while True:
    # Frecuencia del loop
    time.sleep(1.0)
    try:
        # Solicita una imagen a la ESP32-CAM
        response = requests.get(esp32_url, stream=True)
        if response.status_code == 200:
            # Convertimos los datos como buffer de bytes (Numpy) que nos han enviado de la petición HTTP GET
            data = np.frombuffer(response.content, np.uint8)
            # Convertimos el buffer de bytes a imagen válida para OpenCV
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
            # Imagen a escala de grises, no necesitamos color, simplificamos memoria de cálculos
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Usamos Canny para dejar toda la imagen en negro y en blanco todos los contornos que encuentre
            edges1 = cv2.Canny(gray_image, 100, 200)
            # Generamos una lista con todos los contornos
            contours, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Creamos un buffer B/W todo negro como máscara, compatible imagen OpenCV para pintar encima (solo grises)
            mask = np.zeros_like(gray_image)  # Crear una nueva imagen en blanco del tamaño de la captura vacía para poder dibujar
            # Una copia de la imagen para dibujar encima el resultado
            mask_resultado = image.copy()
            # Trabajamos con los contornos que hemos encontrado (primera vuelta) (eliminamos estrellas, no convexos)
            contornos_candidatos = []
            for contour in contours:
                if cv2.contourArea(contour) > 150:  # Filtrar áreas pequeñas
                    # Aproximar el contorno
                    epsilon = 0.025 * cv2.arcLength(contour, True)  # Mayor el 0.1 más aproximación hace, menos puntos de contorno
                    aproximacion = cv2.approxPolyDP(contour, epsilon, True)
                    x, y, w, h = cv2.boundingRect(aproximacion)
                    # Adicional: opcional si quieres contornos convexos
                    if cv2.isContourConvex(aproximacion):
                        contornos_candidatos.append(contour)
                    else:
                        cv2.drawContours(mask, [contour], -1, 255, thickness=1)  # Dibuja en blanco sobre la máscara
                else:
                    cv2.drawContours(mask, [contour], -1, 128, thickness=1)  # Dibuja en gris sobre la máscara

            # Trabajamos con los contornos que hemos encontrado (SEGUNDA vuelta)
            contornos_candidatos2 = []
            for contour in contornos_candidatos:
                # Aproximar el contorno
                epsilon = 0.07 * cv2.arcLength(contour, True)  # Con este valor me discrimina el cuadrado 4
                aproximacion = cv2.approxPolyDP(contour, epsilon, True)
                x, y, w, h = cv2.boundingRect(aproximacion)
                # Calcular el centro del bounding box
                centro_x = x + w // 2
                centro_y = y + h // 2
                # Verificar si tiene forma rectangular
                if len(aproximacion) == 4:
                    cv2.rectangle(mask_resultado, (x-8, y-8), (x + w + 8, y + h + 8), color=(0, 0, 255), thickness=1)  # COLOR ROJO
                    cv2.putText(mask_resultado, str(len(aproximacion)), (centro_x, centro_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    contornos_candidatos2.append(contour)
                    # Hacer crop de la región
                    cropped_rect = gray_image[y:y+h, x:x+w]
                    cropped_edges = cv2.Canny(cropped_rect, 100, 200)
                    contornosinteriores, _ = cv2.findContours(cropped_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    # Si hay cosas dentro puede ser una matrícula
                    if len(contornosinteriores) > 10:
                        # Enderezar la imagen usando la transformación de perspectiva
                        rectangulo_enderezado = enderezar_imagen(image, aproximacion)
                        # Le quitamos el borde del rectángulo (5 pixels)
                        alto, ancho, canales = rectangulo_enderezado.shape
                        pixelsreduccion = 5
                        rectangulo_sinborde = rectangulo_enderezado[pixelsreduccion:alto-pixelsreduccion, pixelsreduccion:ancho-pixelsreduccion]
                        # Mostrar el recorte de la matrícula
                        cv2.imshow('Recorte de matrícula', rectangulo_sinborde)
                        # Aplicamos OCR
                        texto = pytesseract.image_to_string(rectangulo_sinborde, lang='eng')
                        # Limpiar el texto eliminando espacios en blanco y caracteres no deseados
                        texto_limpio = ''.join(e for e in texto if e.isalnum())
                        # Verificar si el texto tiene una longitud mínima adecuada para ser una matrícula
                        if len(texto_limpio) >= 5:  # Ajusta este valor según el formato de las matrículas esperadas
                            print("¡Matrícula detectada!")
                            print(f"Texto de la matrícula: {texto_limpio}")
                        else:
                            print("Texto detectado pero no parece ser una matrícula.")
                elif len(aproximacion) == 3:  # Verificar si tiene forma triangular
                    cv2.rectangle(mask_resultado, (x-4, y-4), (x + w + 4, y + h + 4), color=(0, 255, 0), thickness=1)  # COLOR VERDE
                    cv2.putText(mask_resultado, str(len(aproximacion)), (centro_x, centro_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    contornos_candidatos2.append(contour)

            # Dibujar los contornos cerrados en la imagen original
            imagen_resultado = image.copy()
            cv2.drawContours(imagen_resultado, contornos_candidatos2, -1, (0, 255, 0), 2)
            # Muestra la imagen
            cv2.imshow("Canny 1", edges1)
            cv2.imshow("Contornos Externos Cerrados", mask)
            cv2.imshow("Debug", mask_resultado)
            cv2.imshow("Resultado final", imagen_resultado)
            # Salir con la tecla 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("Error al obtener la imagen.")
    except Exception as e:
        print(f"Error: {e}")

cv2.destroyAllWindows()