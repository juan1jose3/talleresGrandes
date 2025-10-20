from jsonrpcserver import method, serve,Success


productos = [
    {"id": 1, "nombre": "Sofá Seccional", "categoria": "Sala", "precio": 1200.0, "stock": 5},
    {"id": 2, "nombre": "Mesa de Comedor", "categoria": "Comedor", "precio": 800.0, "stock": 10},
    {"id": 3, "nombre": "Silla de Oficina", "categoria": "Oficina", "precio": 150.0, "stock": 20},
    {"id": 4, "nombre": "Cama Queen", "categoria": "Dormitorio", "precio": 1000.0, "stock": 7},
    {"id": 5, "nombre": "Estantería", "categoria": "Almacenamiento", "precio": 200.0, "stock": 15},
    {"id": 6, "nombre": "Mesa de Centro", "categoria": "Sala", "precio": 250.0, "stock": 12},
    {"id": 7, "nombre": "Silla de Comedor", "categoria": "Comedor", "precio": 120.0, "stock": 30},
    {"id": 8, "nombre": "Escritorio", "categoria": "Oficina", "precio": 350.0, "stock": 8},
    {"id": 9, "nombre": "Armario", "categoria": "Dormitorio", "precio": 600.0, "stock": 4},
    {"id": 10, "nombre": "Taburete", "categoria": "Bar", "precio": 90.0, "stock": 25}
]

@method
def cargar_productos(origen=None):
    if origen:
         print(f"Solicitud recibida de {origen}")
    return Success(productos)


if __name__ == "__main__":
      print("Corriendo inventario :) ")
      serve("172.20.0.3", 5001)
    
    