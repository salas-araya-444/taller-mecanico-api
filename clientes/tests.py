from taller_backend.pruebas_base import PruebaBase
from .models import Cliente


class ClientesTests(PruebaBase):

    def test_recepcionista_crea_cliente(self):
        # CRUD: crear
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/clientes/', {
            'nombre': 'Nuevo Cliente', 'cedula': '622223333',
            'telefono': '87776655', 'correo': 'nuevo@correo-ficticio.com'
        }, format='json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(Cliente.objects.filter(cedula='622223333').exists())

    def test_cedula_duplicada_devuelve_400(self):
        # Regla de negocio: la cédula es única
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/clientes/', {
            'nombre': 'Otro', 'cedula': self.cliente.cedula,
            'telefono': '87776655', 'correo': 'otro@correo-ficticio.com'
        }, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('cedula', respuesta.data)

    def test_sin_token_devuelve_401(self):
        # Permisos: sin autenticación
        self.sin_autenticar()
        respuesta = self.client.get('/api/clientes/')
        self.assertEqual(respuesta.status_code, 401)

    def test_mecanico_no_puede_crear_cliente(self):
        # Permisos: el mecánico solo consulta clientes
        self.autenticar(self.mecanico)
        respuesta = self.client.post('/api/clientes/', {
            'nombre': 'X', 'cedula': '633334444',
            'telefono': '87776655', 'correo': 'x@correo-ficticio.com'
        }, format='json')
        self.assertEqual(respuesta.status_code, 403)

    def test_busqueda_y_paginacion(self):
        # Paginación de 5 en 5 y búsqueda parcial
        for i in range(7):
            Cliente.objects.create(
                nombre=f'Persona Ficticia {i}', cedula=f'70000000{i}',
                telefono='88880000', correo=f'p{i}@correo-ficticio.com'
            )
        self.autenticar(self.mecanico)
        respuesta = self.client.get('/api/clientes/?buscar=persona&page=2')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['pagina_actual'], 2)
        self.assertEqual(respuesta.data['total_paginas'], 2)
        self.assertEqual(respuesta.data['total_registros'], 7)
        self.assertEqual(len(respuesta.data['resultados']), 2)

    def test_eliminar_cliente_con_vehiculos_devuelve_409(self):
        # PROTECT: no se borra un cliente con vehículos
        self.autenticar(self.admin)
        respuesta = self.client.delete(f'/api/clientes/{self.cliente.id}/')
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(Cliente.objects.filter(id=self.cliente.id).exists())
