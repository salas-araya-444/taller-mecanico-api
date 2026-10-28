from taller_backend.pruebas_base import PruebaBase
from .models import Repuesto


class RepuestosTests(PruebaBase):

    def test_admin_crea_y_recepcionista_no(self):
        datos = {'codigo': 'NV-001', 'nombre': 'Filtro nuevo', 'precio': '5000.00', 'stock': 5, 'stock_minimo': 1}

        self.autenticar(self.recepcion)
        self.assertEqual(self.client.post('/api/repuestos/', datos, format='json').status_code, 403)

        self.autenticar(self.admin)
        respuesta = self.client.post('/api/repuestos/', datos, format='json')
        self.assertEqual(respuesta.status_code, 201)

    def test_precio_negativo_y_stock_negativo_por_patch(self):
        # Regla de negocio protegida también en PATCH
        self.autenticar(self.admin)
        respuesta = self.client.patch(f'/api/repuestos/{self.repuesto.id}/', {'precio': '-100'}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.patch(f'/api/repuestos/{self.repuesto.id}/', {'stock': -3}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_ordenar_por_precio_descendente(self):
        Repuesto.objects.create(codigo='CA-100', nombre='Caro', precio=90000, stock=1)
        Repuesto.objects.create(codigo='BA-100', nombre='Barato', precio=100, stock=1)
        self.autenticar(self.mecanico)
        respuesta = self.client.get('/api/repuestos/?ordenar=-precio')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['resultados'][0]['codigo'], 'CA-100')

    def test_buscar_repuesto_por_nombre(self):
        Repuesto.objects.create(codigo='BJ-001', nombre='Bujia', precio=1000, stock=1)
        self.autenticar(self.mecanico)
        respuesta = self.client.get('/api/repuestos/?buscar=buj')
        self.assertEqual(respuesta.data['total_registros'], 1)
        self.assertEqual(respuesta.data['resultados'][0]['codigo'], 'BJ-001')

    def test_eliminar_repuesto_sin_uso(self):
        # CRUD: eliminar
        self.autenticar(self.admin)
        respuesta = self.client.delete(f'/api/repuestos/{self.repuesto.id}/')
        self.assertEqual(respuesta.status_code, 204)
        self.assertFalse(Repuesto.objects.filter(id=self.repuesto.id).exists())
