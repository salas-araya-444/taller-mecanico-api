from django.core.paginator import Paginator
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ordenes.models import OrdenServicio
from ordenes.serializers import OrdenServicioSerializer
from taller_backend.utilidades import tiene_rol
from .models import Vehiculo
from .serializers import VehiculoSerializer

#-----------------------------------------------------------------------------------------------

def respuesta_paginada(queryset, page_number):
    paginator = Paginator(queryset, 5)
    page = paginator.get_page(page_number)
    serializer = VehiculoSerializer(page.object_list, many=True)
    return Response({
        'pagina_actual': page.number,
        'total_paginas': paginator.num_pages,
        'total_registros': paginator.count,
        'resultados': serializer.data
    })

#-----------------------------------------------------------------------------------------------

# El listado tiene filtros que se pueden combinar (cliente, marca y año)
# y búsqueda parcial por placa.

@api_view(['GET', 'POST'])
def vehiculos_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        vehiculos = Vehiculo.objects.order_by('placa')
        cliente = request.query_params.get('cliente')
        marca = request.query_params.get('marca')
        anio = request.query_params.get('anio')
        buscar = request.query_params.get('buscar')

        if cliente:
            vehiculos = vehiculos.filter(cliente_id=cliente)
        if marca:
            vehiculos = vehiculos.filter(marca__iexact=marca)
        if anio:
            if not anio.isdigit():
                return Response({'anio': 'El año debe ser un número...'}, status=status.HTTP_400_BAD_REQUEST)
            vehiculos = vehiculos.filter(anio=anio)
        if buscar:
            vehiculos = vehiculos.filter(placa__icontains=buscar)

        return respuesta_paginada(vehiculos, request.query_params.get('page', 1))

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    serializer = VehiculoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-----------------------------------------------------------------------------------------------

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def vehiculo_detalle_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        vehiculo = Vehiculo.objects.get(id=id)
    except Vehiculo.DoesNotExist:
        return Response({'error': 'Vehículo no encontrado...'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(VehiculoSerializer(vehiculo).data)

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        serializer = VehiculoSerializer(
            vehiculo, data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Un vehículo con órdenes no se puede borrar (on_delete=PROTECT)
    try:
        vehiculo.delete()
    except ProtectedError:
        return Response({'error': 'No se puede eliminar el vehículo porque tiene órdenes...'}, status=status.HTTP_409_CONFLICT)

    return Response(status=status.HTTP_204_NO_CONTENT)

#-----------------------------------------------------------------------------------------------

# Historial de un vehículo: todas sus órdenes con los repuestos usados.

@api_view(['GET'])
def historial_vehiculo_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        vehiculo = Vehiculo.objects.get(id=id)
    except Vehiculo.DoesNotExist:
        return Response({'error': 'Vehículo no encontrado...'}, status=status.HTTP_404_NOT_FOUND)

    # select_related trae el mecánico en la misma consulta.
    # prefetch_related trae los repuestos de todas las órdenes de una vez,
    # en lugar de hacer una consulta por cada orden.
    ordenes = OrdenServicio.objects.filter(vehiculo=vehiculo).select_related(
        'mecanico'
    ).prefetch_related('detalles').order_by('-fecha_ingreso')

    return Response({
        'vehiculo': VehiculoSerializer(vehiculo).data,
        'ordenes': OrdenServicioSerializer(ordenes, many=True).data
    })

#-----------------------------------------------------------------------------------------------
