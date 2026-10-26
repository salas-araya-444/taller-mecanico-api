from rest_framework import serializers
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['fecha_registro']

#-----------------------------------------------------------------------------------------------

    def validate_cedula(self, value):
        if not value.isdigit() or len(value) < 9:
            raise serializers.ValidationError('La cédula debe tener solo números y al menos 9 dígitos...')
        return value

    def validate_telefono(self, value):
        if not value.isdigit() or len(value) < 8:
            raise serializers.ValidationError('El teléfono debe tener al menos 8 dígitos...')
        return value

#-----------------------------------------------------------------------------------------------
