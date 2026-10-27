from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from taller_backend.utilidades import tiene_rol, es_mecanico
from .models import OrdenServicio, DetalleOrden
from .serializers import OrdenServicioSerializer, DetalleOrdenSerializer

#-----------------------------------------------------------------------------------------------

def respuesta_paginada(queryset, page_number):
    paginator = Paginator(queryset, 5)
    page = paginator.get_page(page_number)
    serializer = OrdenServicioSerializer(page.object_list, many=True)
    return Response({
        'pagina_actual': page.number,
        'total_paginas': paginator.num_pages,
        'total_registros': paginator.count,
        'resultados': serializer.data
    })

#-----------------------------------------------------------------------------------------------

# Listado con filtros que se pueden combinar: estado, mecánico y vehículo.
# El mecánico solo ve las órdenes que tiene asignadas.

@api_view(['GET', 'POST'])
def ordenes_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        ordenes = OrdenServicio.objects.order_by('-fecha_ingreso')
        estado = request.query_params.get('estado')
        mecanico = request.query_params.get('mecanico')
        vehiculo = request.query_params.get('vehiculo')

        if es_mecanico(request.user):
            ordenes = ordenes.filter(mecanico=request.user)

        if estado:
            ordenes = ordenes.filter(estado=estado.upper())
        if mecanico:
            ordenes = ordenes.filter(mecanico_id=mecanico)
        if vehiculo:
            ordenes = ordenes.filter(vehiculo_id=vehiculo)

        return respuesta_paginada(ordenes, request.query_params.get('page', 1))

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    serializer = OrdenServicioSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-----------------------------------------------------------------------------------------------

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def orden_detalle_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        orden = OrdenServicio.objects.get(id=id)
    except OrdenServicio.DoesNotExist:
        return Response({'error': 'Orden no encontrada...'}, status=status.HTTP_404_NOT_FOUND)

    # Un mecánico solo puede ver sus propias órdenes
    if es_mecanico(request.user) and orden.mecanico != request.user:
        return Response({'detail': 'Esta orden es de otro mecánico...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(OrdenServicioSerializer(orden).data)

    if request.method in ['PUT', 'PATCH']:
        if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
            return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

        # Una orden facturada ya no se puede modificar
        if orden.estado == 'FACTURADA':
            return Response({'error': 'La orden ya fue facturada y no se puede modificar...'}, status=status.HTTP_409_CONFLICT)

        if 'estado' in request.data:
            return Response({'estado': 'El estado se cambia con /cambiar-estado/...'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrdenServicioSerializer(
            orden, data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if not tiene_rol(request.user, ['Administrador']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    # Solo se eliminan órdenes recién abiertas, que todavía no tienen repuestos
    if orden.estado != 'RECIBIDA':
        return Response({'error': 'Solo se pueden eliminar órdenes en estado Recibida...'}, status=status.HTTP_409_CONFLICT)

    orden.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

#-----------------------------------------------------------------------------------------------

# Cambia la orden al siguiente estado: RECIBIDA -> EN_REPARACION -> FINALIZADA.
# Al finalizar también se puede enviar la mano de obra.

@api_view(['POST'])
def cambiar_estado_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if not tiene_rol(request.user, ['Administrador', 'Mecanico']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    try:
        orden = OrdenServicio.objects.get(id=id)
    except OrdenServicio.DoesNotExist:
        return Response({'error': 'Orden no encontrada...'}, status=status.HTTP_404_NOT_FOUND)

    if es_mecanico(request.user) and orden.mecanico != request.user:
        return Response({'detail': 'Esta orden es de otro mecánico...'}, status=status.HTTP_403_FORBIDDEN)

    if orden.estado == 'FACTURADA':
        return Response({'error': 'La orden ya fue facturada y no se puede modificar...'}, status=status.HTTP_409_CONFLICT)

    nuevo_estado = request.data.get('estado', '').upper()

    # Revisamos que el nuevo estado sea el siguiente permitido
    if orden.estado == 'RECIBIDA' and nuevo_estado != 'EN_REPARACION':
        return Response({'estado': 'Desde RECIBIDA solo se puede pasar a EN_REPARACION...'}, status=status.HTTP_400_BAD_REQUEST)

    if orden.estado == 'EN_REPARACION' and nuevo_estado != 'FINALIZADA':
        return Response({'estado': 'Desde EN_REPARACION solo se puede pasar a FINALIZADA...'}, status=status.HTTP_400_BAD_REQUEST)

    if orden.estado == 'FINALIZADA':
        return Response({'estado': 'La orden ya está finalizada, ahora se debe facturar...'}, status=status.HTTP_400_BAD_REQUEST)

    if nuevo_estado == 'FINALIZADA':
        mano_obra = request.data.get('mano_obra')
        if mano_obra is not None:
            try:
                mano_obra = float(mano_obra)
            except ValueError:
                return Response({'mano_obra': 'La mano de obra debe ser un número...'}, status=status.HTTP_400_BAD_REQUEST)
            if mano_obra < 0:
                return Response({'mano_obra': 'La mano de obra no puede ser negativa...'}, status=status.HTTP_400_BAD_REQUEST)
            orden.mano_obra = mano_obra
        orden.fecha_finalizacion = timezone.now()

    orden.estado = nuevo_estado
    orden.save()
    orden.refresh_from_db()
    return Response(OrdenServicioSerializer(orden).data)

#-----------------------------------------------------------------------------------------------

# Repuestos usados en una orden (tabla intermedia DetalleOrden)

@api_view(['GET', 'POST'])
def detalles_orden_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        orden = OrdenServicio.objects.get(id=id)
    except OrdenServicio.DoesNotExist:
        return Response({'error': 'Orden no encontrada...'}, status=status.HTTP_404_NOT_FOUND)

    if es_mecanico(request.user) and orden.mecanico != request.user:
        return Response({'detail': 'Esta orden es de otro mecánico...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(DetalleOrdenSerializer(orden.detalles.all(), many=True).data)

    if not tiene_rol(request.user, ['Administrador', 'Mecanico']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    if orden.estado == 'FACTURADA':
        return Response({'error': 'La orden ya fue facturada y no se puede modificar...'}, status=status.HTTP_409_CONFLICT)

    if orden.estado != 'EN_REPARACION':
        return Response({'error': 'Solo se agregan repuestos cuando la orden está En reparación...'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = DetalleOrdenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    repuesto = serializer.validated_data['repuesto']
    cantidad = serializer.validated_data['cantidad']

    if orden.detalles.filter(repuesto=repuesto).exists():
        return Response({'repuesto': 'Este repuesto ya está en la orden, modifique la cantidad...'}, status=status.HTTP_400_BAD_REQUEST)

    if cantidad > repuesto.stock:
        return Response({'cantidad': 'No hay suficiente stock de este repuesto...'}, status=status.HTTP_400_BAD_REQUEST)

    # Se descuenta del inventario y se guarda el precio que tiene el repuesto hoy
    repuesto.stock = repuesto.stock - cantidad
    repuesto.save()
    serializer.save(orden=orden, precio_aplicado=repuesto.precio)

    return Response(serializer.data, status=status.HTTP_201_CREATED)

#-----------------------------------------------------------------------------------------------

# Consultar, cambiar la cantidad o quitar un repuesto de la orden

@api_view(['GET', 'PATCH', 'DELETE'])
def detalle_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        detalle = DetalleOrden.objects.get(id=id)
    except DetalleOrden.DoesNotExist:
        return Response({'error': 'Detalle no encontrado...'}, status=status.HTTP_404_NOT_FOUND)

    orden = detalle.orden
    repuesto = detalle.repuesto

    if es_mecanico(request.user) and orden.mecanico != request.user:
        return Response({'detail': 'Esta orden es de otro mecánico...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(DetalleOrdenSerializer(detalle).data)

    if not tiene_rol(request.user, ['Administrador', 'Mecanico']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    if orden.estado == 'FACTURADA':
        return Response({'error': 'La orden ya fue facturada y no se puede modificar...'}, status=status.HTTP_409_CONFLICT)

    if orden.estado != 'EN_REPARACION':
        return Response({'error': 'Solo se modifican repuestos cuando la orden está En reparación...'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PATCH':
        # Solo se permite cambiar la cantidad
        serializer = DetalleOrdenSerializer(detalle, data={'cantidad': request.data.get('cantidad')}, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nueva_cantidad = serializer.validated_data['cantidad']

        # Si la cantidad sube se descuenta la diferencia; si baja, se devuelve al inventario
        diferencia = nueva_cantidad - detalle.cantidad
        if diferencia > repuesto.stock:
            return Response({'cantidad': 'No hay suficiente stock de este repuesto...'}, status=status.HTTP_400_BAD_REQUEST)

        repuesto.stock = repuesto.stock - diferencia
        repuesto.save()
        serializer.save()
        return Response(serializer.data)

    # Al quitar el repuesto de la orden, las unidades vuelven al inventario
    repuesto.stock = repuesto.stock + detalle.cantidad
    repuesto.save()
    detalle.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

#-----------------------------------------------------------------------------------------------
