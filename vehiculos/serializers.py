from rest_framework import serializers
from .models import Vehiculo


class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'

#-----------------------------------------------------------------------------------------------

    def validate_anio(self, value):
        if value < 1950 or value > 2027:
            raise serializers.ValidationError('El año debe estar entre 1950 y 2027...')
        return value

#-----------------------------------------------------------------------------------------------
