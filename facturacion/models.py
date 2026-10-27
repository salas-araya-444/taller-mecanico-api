from django.db import models
from ordenes.models import OrdenServicio


class Factura(models.Model):
    # Relación 1:1: cada orden tiene como máximo una factura.
    # PROTECT impide borrar una orden que ya fue facturada.
    orden = models.OneToOneField(
        OrdenServicio,
        on_delete=models.PROTECT,
        related_name='factura'
    )
    numero = models.CharField(max_length=30, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    # Los montos los calcula el sistema al facturar; no se reciben del usuario
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'Factura {self.numero}'
