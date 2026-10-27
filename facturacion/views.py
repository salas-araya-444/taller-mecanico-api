from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, F, Sum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ordenes.models import OrdenServicio
from repuestos.models import Repuesto
from taller_backend.utilidades import tiene_rol
from .models import Factura
from .serializers import FacturaSerializer

#-----------------------------------------------------------------------------------------------

def respuesta_paginada(queryset, page_number):
    paginator = Paginator(queryset, 5)
    page = paginator.get_page(page_number)
    serializer = FacturaSerializer(page.object_list, many=True)
    return Response({
        'pagina_actual': page.number,
        'total_paginas': paginator.num_pages,
        'total_registros': paginator.count,
        'resultados': serializer.data
    })

#-----------------------------------------------------------------------------------------------

# Para facturar solo se envía la orden. El sistema calcula subtotal, IVA (13 %) y total.

@api_view(['GET', 'POST'])
def facturas_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        facturas = Factura.objects.order_by('-fecha')
        cliente = request.query_params.get('cliente')

        # Filtro a través de las relaciones: factura -> orden -> vehículo -> cliente
        if cliente:
            facturas = facturas.filter(orden__vehiculo__cliente_id=cliente)

        return respuesta_paginada(facturas, request.query_params.get('page', 1))

    # Una orden solo se puede facturar una vez
    orden_id = str(request.data.get('orden', ''))
    if orden_id.isdigit() and Factura.objects.filter(orden_id=orden_id).exists():
        return Response({'error': 'Esta orden ya fue facturada...'}, status=status.HTTP_409_CONFLICT)

    serializer = FacturaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    orden = serializer.validated_data['orden']

    # subtotal = mano de obra + (cantidad x precio) de cada repuesto usado
    subtotal = orden.mano_obra
    for detalle in orden.detalles.all():
        subtotal = subtotal + detalle.cantidad * detalle.precio_aplicado

    iva = round(subtotal * 13 / 100, 2)
    total = subtotal + iva

    # Número consecutivo de la factura: FAC-1, FAC-2, ...
    numero = 'FAC-' + str(Factura.objects.count() + 1)

    serializer.save(numero=numero, subtotal=subtotal, iva=iva, total=total)

    # Al facturar, la orden queda cerrada
    orden.estado = 'FACTURADA'
    orden.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)

#-----------------------------------------------------------------------------------------------

# Una factura no se modifica ni se elimina, para conservar el historial.
# Por eso este módulo solo permite crear y consultar.

@api_view(['GET'])
def factura_detalle_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    try:
        factura = Factura.objects.get(id=id)
    except Factura.DoesNotExist:
        return Response({'error': 'Factura no encontrada...'}, status=status.HTTP_404_NOT_FOUND)

    return Response(FacturaSerializer(factura).data)

#-----------------------------------------------------------------------------------------------

# Reportes para el administrador

@api_view(['GET'])
def reportes_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if not tiene_rol(request.user, ['Administrador']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    # Repuestos con stock menor o igual al mínimo.
    # F('stock_minimo') permite comparar dos campos del mismo repuesto.
    bajo_stock = Repuesto.objects.filter(stock__lte=F('stock_minimo')).values('codigo', 'nombre', 'stock')

    # Repuestos más usados: annotate agrega a cada repuesto la suma de cantidades usadas en las órdenes
    mas_usados = Repuesto.objects.annotate(total_usado=Sum('detalles_orden__cantidad')).filter(
        total_usado__gt=0
    ).order_by('-total_usado').values('codigo', 'nombre', 'total_usado')

    # Cantidad de órdenes asignadas a cada mecánico
    por_mecanico = User.objects.filter(groups__name='Mecanico').annotate(
        total_ordenes=Count('ordenes_asignadas')
    ).values('username', 'total_ordenes')

    # Cantidad de órdenes en cada estado (agrupa por estado y cuenta)
    por_estado = OrdenServicio.objects.values('estado').annotate(cantidad=Count('id'))

    # Total facturado: aggregate calcula un solo resultado con todas las facturas
    facturacion = Factura.objects.aggregate(cantidad_facturas=Count('id'), total_facturado=Sum('total'))

    return Response({
        'repuestos_bajo_stock': list(bajo_stock),
        'repuestos_mas_usados': list(mas_usados),
        'ordenes_por_mecanico': list(por_mecanico),
        'ordenes_por_estado': list(por_estado),
        'facturacion': facturacion,
    })

#-----------------------------------------------------------------------------------------------
