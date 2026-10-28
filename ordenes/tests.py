
from taller_backend.pruebas_base import PruebaBase
from .models import OrdenServicio, DetalleOrden


class OrdenesTests(PruebaBase):

    def test_crear_orden_inicia_en_recibida(self):
        # CRUD: crear
        orden_id = self.crear_orden()
        orden = OrdenServicio.objects.get(id=orden_id)
        self.assertEqual(orden.estado, 'RECIBIDA')

    def test_no_permite_dos_ordenes_abiertas_para_el_mismo_vehiculo(self):
        self.crear_orden()
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/ordenes/', {
            'vehiculo': self.vehiculo.id, 'mecanico': self.mecanico.id,
            'falla_reportada': 'Otra falla'
        }, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('vehiculo', respuesta.data)

    def test_mecanico_asignado_debe_tener_rol_mecanico(self):
        self.autenticar(self.recepcion)
        respuesta = self.client.post('/api/ordenes/', {
            'vehiculo': self.vehiculo.id, 'mecanico': self.recepcion.id,
            'falla_reportada': 'Ruido'
        }, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('mecanico', respuesta.data)

    def test_no_se_agregan_repuestos_si_no_esta_en_reparacion(self):
        orden_id = self.crear_orden('RECIBIDA')
        self.autenticar(self.mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 1}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_agregar_repuesto_descuenta_stock_y_guarda_precio(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 3}, format='json')
        self.assertEqual(respuesta.status_code, 201)

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock, 7)

        # Si el precio del inventario cambia, el detalle conserva el precio aplicado
        self.repuesto.precio = 15000
        self.repuesto.save()
        detalle = DetalleOrden.objects.get(id=respuesta.data['id'])
        self.assertEqual(detalle.precio_aplicado, 10000)

    def test_stock_insuficiente_devuelve_400(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 50}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock, 10)

    def test_cantidad_cero_devuelve_400(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 0}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_modificar_y_eliminar_detalle_mantiene_stock_coherente(self):
        orden_id = self.crear_orden('EN_REPARACION')
        self.autenticar(self.mecanico)
        detalle_id = self.client.post(
            f'/api/ordenes/{orden_id}/detalles/', {'repuesto': self.repuesto.id, 'cantidad': 3}, format='json'
        ).data['id']

        # Baja de 3 a 2: se devuelve 1 unidad (stock 7 -> 8)
        respuesta = self.client.patch(f'/api/ordenes/detalles/{detalle_id}/', {'cantidad': 2}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock, 8)

        # Al eliminar el detalle vuelven las 2 unidades (stock 10)
        respuesta = self.client.delete(f'/api/ordenes/detalles/{detalle_id}/')
        self.assertEqual(respuesta.status_code, 204)
        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock, 10)

    def test_no_se_puede_saltar_estados(self):
        orden_id = self.crear_orden('RECIBIDA')
        self.autenticar(self.mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/cambiar-estado/', {'estado': 'FINALIZADA'}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_mecanico_no_asignado_recibe_403(self):
        orden_id = self.crear_orden('RECIBIDA', mecanico=self.mecanico)
        self.autenticar(self.otro_mecanico)
        respuesta = self.client.post(f'/api/ordenes/{orden_id}/cambiar-estado/', {'estado': 'EN_REPARACION'}, format='json')
        self.assertEqual(respuesta.status_code, 403)

    def test_patch_no_permite_cambiar_estado_directamente(self):
        orden_id = self.crear_orden('RECIBIDA')
        self.autenticar(self.recepcion)
        respuesta = self.client.patch(f'/api/ordenes/{orden_id}/', {'estado': 'FINALIZADA'}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(OrdenServicio.objects.get(id=orden_id).estado, 'RECIBIDA')

    def test_filtro_por_estado_en_listado(self):
        self.crear_orden('EN_REPARACION')
        self.autenticar(self.admin)
        respuesta = self.client.get('/api/ordenes/?estado=en_reparacion')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['total_registros'], 1)
        respuesta = self.client.get('/api/ordenes/?estado=recibida')
        self.assertEqual(respuesta.data['total_registros'], 0)
