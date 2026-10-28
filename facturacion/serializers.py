from rest_framework import serializers
from .models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = '__all__'
        # Solo se envía la orden; el número y los montos los calcula el sistema
        read_only_fields = ['numero', 'fecha', 'subtotal', 'iva', 'total']

#-----------------------------------------------------------------------------------------------

    def validate_orden(self, value):
        if value.estado != 'FINALIZADA':
            raise serializers.ValidationError('Solo se pueden facturar órdenes finalizadas...')
        return value

#-----------------------------------------------------------------------------------------------
