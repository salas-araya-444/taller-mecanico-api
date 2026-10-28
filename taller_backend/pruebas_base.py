# Preparación común para las pruebas automatizadas.
# Crea un usuario por rol (y un segundo mecánico), sus tokens y algunos datos.
# Cada archivo tests.py usa esta clase para no repetir esta preparación.

from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from clientes.models import Cliente
from repuestos.models import Repuesto
from vehiculos.models import Vehiculo


class PruebaBase(APITestCase):

    def setUp(self):
        self.admin = self.crear_usuario('admin_prueba', 'Administrador')
        self.recepcion = self.crear_usuario('recepcion_prueba', 'Recepcionista')
        self.mecanico = self.crear_usuario('mecanico_prueba', 'Mecanico')
        self.otro_mecanico = self.crear_usuario('mecanico_dos', 'Mecanico')

        self.cliente = Cliente.objects.create(
            nombre='Cliente Prueba', cedula='611112222',
            telefono='88889999', correo='cliente@ejemplo.com'
        )
        self.vehiculo = Vehiculo.objects.create(
            cliente=self.cliente, placa='TST100', marca='Toyota',
            modelo='Yaris', anio=2018, kilometraje=50000
        )
        self.repuesto = Repuesto.objects.create(
            codigo='PR-001', nombre='Pastillas de prueba',
            precio=10000, stock=10, stock_minimo=2
        )

    def crear_usuario(self, username, rol):
        grupo = Group.objects.filter(name=rol).first()
        if grupo is None:
            grupo = Group.objects.create(name=rol)
        usuario = User.objects.create_user(username=username, password='Prueba2026*')
        usuario.groups.add(grupo)
        Token.objects.create(user=usuario)
        return usuario

    def autenticar(self, usuario):
        # Envía el token igual que en Postman: Authorization: Token <clave>
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + usuario.auth_token.key)

    def sin_autenticar(self):
        self.client.credentials()

    def crear_orden(self, estado='RECIBIDA', mecanico=None):
        # Abre una orden y, si se pide, la avanza hasta el estado indicado
        if mecanico is None:
            mecanico = self.mecanico

        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/ordenes/', {
            'vehiculo': self.vehiculo.id,
            'mecanico': mecanico.id,
            'falla_reportada': 'Ruido al frenar'
        }, format='json')
        orden_id = respuesta.data['id']
        url = '/api/ordenes/' + str(orden_id) + '/cambiar-estado/'

        self.autenticar(self.admin)
        if estado == 'EN_REPARACION' or estado == 'FINALIZADA':
            self.client.post(url, {'estado': 'EN_REPARACION'}, format='json')
        if estado == 'FINALIZADA':
            self.client.post(url, {'estado': 'FINALIZADA', 'mano_obra': 20000}, format='json')

        return orden_id
