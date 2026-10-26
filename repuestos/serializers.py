from rest_framework import serializers
from .models import Repuesto


class RepuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repuesto
        fields = '__all__'

#-----------------------------------------------------------------------------------------------

    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError('El precio no puede ser negativo...')
        return value

#-----------------------------------------------------------------------------------------------
