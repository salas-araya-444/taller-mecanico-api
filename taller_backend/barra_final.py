# Postman a veces quita la barra final de las direcciones al importar la colección
# (envía /api/token en vez de /api/token/). Todas nuestras rutas terminan en "/",
# así que este middleware se la agrega antes de buscar la ruta.

class BarraFinalMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path_info.endswith('/'):
            request.path_info = request.path_info + '/'
        return self.get_response(request)
