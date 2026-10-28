from taller_backend.pruebas_base import PruebaBase
from .models import Vehiculo


class VehiculosTests(PruebaBase):

    def test_crear_vehiculo(self):
        # CRUD: crear
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/vehiculos/', {
            'cliente': self.cliente.id, 'placa': 'ABC123', 'marca': 'Nissan',
            'modelo': 'Versa', 'anio': 2020, 'kilometraje': 15000
        }, format='json')
        self.assertEqual(respuesta.status_code, 201)

    def test_placa_duplicada_devuelve_400(self):
        # Regla de negocio: la placa es única
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/vehiculos/', {
            'cliente': self.cliente.id, 'placa': 'TST100', 'marca': 'Kia',
            'modelo': 'Rio', 'anio': 2015
        }, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('placa', respuesta.data)

    def test_patch_kilometraje(self):
        # CRUD: actualización parcial
        self.autenticar(self.recepcion)
        respuesta = self.client.patch(f'/api/vehiculos/{self.vehiculo.id}/', {'kilometraje': 52000}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.kilometraje, 52000)

    def test_filtros_combinados_marca_y_cliente(self):
        Vehiculo.objects.create(
            cliente=self.cliente, placa='TST200', marca='Honda',
            modelo='Civic', anio=2019
        )
        self.autenticar(self.mecanico)
        respuesta = self.client.get(f'/api/vehiculos/?cliente={self.cliente.id}&marca=toyota')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['total_registros'], 1)
        self.assertEqual(respuesta.data['resultados'][0]['placa'], 'TST100')

    def test_historial_muestra_ordenes_y_repuestos(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.mecanico)
        self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 2}, format='json')

        respuesta = self.client.get(f'/api/vehiculos/{self.vehiculo.id}/historial/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data['ordenes']), 1)
        self.assertEqual(len(respuesta.data['ordenes'][0]['detalles']), 1)
