from ordenes.models import OrdenServicio
from taller_backend.pruebas_base import PruebaBase
from .models import Factura


class FacturacionTests(PruebaBase):

    def orden_finalizada_con_repuestos(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.mecanico)
        # 2 unidades de 10 000 = 20 000 en repuestos
        self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 2}, format='json')
        # Mano de obra: 20 000
        self.client.post(f'/api/ordenes/{orden_id}/cambiar-estado/', {'estado': 'FINALIZADA', 'mano_obra': '20000'}, format='json')
        return orden_id

    def test_no_se_factura_orden_no_finalizada(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/facturas/', {'orden': orden_id}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_factura_calcula_totales_y_cierra_la_orden(self):
        orden_id = self.orden_finalizada_con_repuestos()
        self.autenticar(self.recepcion)
        # Aunque se envíe un total, el sistema lo ignora y lo calcula
        respuesta = self.client.post('/api/facturas/', {'orden': orden_id, 'total': '1'}, format='json')
        self.assertEqual(respuesta.status_code, 201)

        factura = Factura.objects.get(orden_id=orden_id)
        self.assertEqual(factura.subtotal, 40000)  # 20 000 + 20 000
        self.assertEqual(factura.iva, 5200)        # 13 %
        self.assertEqual(factura.total, 45200)
        self.assertEqual(OrdenServicio.objects.get(id=orden_id).estado, 'FACTURADA')

    def test_no_se_factura_dos_veces(self):
        orden_id = self.orden_finalizada_con_repuestos()
        self.autenticar(self.recepcion)
        self.client.post('/api/facturas/', {'orden': orden_id}, format='json')
        respuesta = self.client.post('/api/facturas/', {'orden': orden_id}, format='json')
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(Factura.objects.filter(orden_id=orden_id).count(), 1)

    def test_orden_facturada_no_se_modifica(self):
        orden_id = self.orden_finalizada_con_repuestos()
        self.autenticar(self.recepcion)
        self.client.post('/api/facturas/', {'orden': orden_id}, format='json')

        respuesta = self.client.patch(f'/api/ordenes/{orden_id}/', {'mano_obra': '1'}, format='json')
        self.assertEqual(respuesta.status_code, 409)

        self.autenticar(self.mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 1}, format='json')
        self.assertEqual(respuesta.status_code, 409)

    def test_mecanico_no_puede_facturar(self):
        orden_id = self.orden_finalizada_con_repuestos()
        self.autenticar(self.mecanico)
        respuesta = self.client.post('/api/facturas/', {'orden': orden_id}, format='json')
        self.assertEqual(respuesta.status_code, 403)

    def test_reportes_solo_para_administrador(self):
        self.orden_finalizada_con_repuestos()
        self.autenticar(self.recepcion)
        self.assertEqual(self.client.get('/api/reportes/').status_code, 403)

        self.autenticar(self.admin)
        respuesta = self.client.get('/api/reportes/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['repuestos_mas_usados'][0]['total_usado'], 2)
