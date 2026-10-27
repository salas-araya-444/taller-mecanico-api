from rest_framework import serializers
from .models import OrdenServicio, DetalleOrden


class DetalleOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleOrden
        fields = '__all__'
        # La orden viene en la URL y el precio lo pone el sistema
        read_only_fields = ['orden', 'precio_aplicado']

#-----------------------------------------------------------------------------------------------

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor que cero...')
        return value

#-----------------------------------------------------------------------------------------------

class OrdenServicioSerializer(serializers.ModelSerializer):
    # Muestra los repuestos usados dentro de la orden (solo lectura)
    detalles = DetalleOrdenSerializer(many=True, read_only=True)

    class Meta:
        model = OrdenServicio
        # "repuestos" se omite porque ya se muestran en "detalles"
        exclude = ['repuestos']
        # El estado solo cambia con /cambiar-estado/ o al facturar
        read_only_fields = ['estado', 'fecha_ingreso', 'fecha_finalizacion']

#-----------------------------------------------------------------------------------------------

    def validate_mecanico(self, value):
        if not value.groups.filter(name='Mecanico').exists():
            raise serializers.ValidationError('El usuario asignado debe tener el rol de mecánico...')
        return value

    def validate_mano_obra(self, value):
        if value < 0:
            raise serializers.ValidationError('La mano de obra no puede ser negativa...')
        return value

    def validate(self, data):
        vehiculo = data.get('vehiculo')

        # Un vehículo no puede tener dos órdenes abiertas (abierta = todavía no facturada)
        if vehiculo:
            abiertas = OrdenServicio.objects.filter(vehiculo=vehiculo).exclude(estado='FACTURADA')
            if self.instance:
                abiertas = abiertas.exclude(id=self.instance.id)
            if abiertas.exists():
                raise serializers.ValidationError({'vehiculo': 'Este vehículo ya tiene una orden abierta...'})

        return data

#-----------------------------------------------------------------------------------------------
