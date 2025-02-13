from app import create_app 

app = create_app()
# Inicializar base de datos y ejecutar la aplicación
if __name__ == "__main__":
    
    app.run(host='0.0.0.0', port=81, debug=True)
