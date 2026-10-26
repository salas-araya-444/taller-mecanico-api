from django.core.paginator import Paginator
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from taller_backend.utilidades import tiene_rol
from .models import Repuesto
from .serializers import RepuestoSerializer

#-----------------------------------------------------------------------------------------------

def respuesta_paginada(queryset, page_number):
    paginator = Paginator(queryset, 5)
    page = paginator.get_page(page_number)
    serializer = RepuestoSerializer(page.object_list, many=True)
    return Response({
        'pagina_actual': page.number,
        'total_paginas': paginator.num_pages,
        'total_registros': paginator.count,
        'resultados': serializer.data
    })

#-----------------------------------------------------------------------------------------------

# Todos pueden consultar el inventario. Solo el administrador lo modifica.
# El listado permite buscar por nombre y ordenar por nombre, precio o stock.

@api_view(['GET', 'POST'])
def repuestos_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        repuestos = Repuesto.objects.order_by('nombre')
        buscar = request.query_params.get('buscar')
        ordenar = request.query_params.get('ordenar')

        if buscar:
            repuestos = repuestos.filter(nombre__icontains=buscar)

        # El "-" adelante ordena de mayor a menor (por ejemplo: -precio)
        if ordenar in ['nombre', 'precio', '-precio', 'stock', '-stock']:
            repuestos = repuestos.order_by(ordenar)

        return respuesta_paginada(repuestos, request.query_params.get('page', 1))

    if not tiene_rol(request.user, ['Administrador']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    serializer = RepuestoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-----------------------------------------------------------------------------------------------

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def repuesto_detalle_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        repuesto = Repuesto.objects.get(id=id)
    except Repuesto.DoesNotExist:
        return Response({'error': 'Repuesto no encontrado...'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(RepuestoSerializer(repuesto).data)

    if not tiene_rol(request.user, ['Administrador']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        serializer = RepuestoSerializer(
            repuesto, data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Un repuesto que ya se usó en órdenes no se puede borrar (on_delete=PROTECT)
    try:
        repuesto.delete()
    except ProtectedError:
        return Response({'error': 'No se puede eliminar el repuesto porque ya se usó en órdenes...'}, status=status.HTTP_409_CONFLICT)

    return Response(status=status.HTTP_204_NO_CONTENT)

#-----------------------------------------------------------------------------------------------
