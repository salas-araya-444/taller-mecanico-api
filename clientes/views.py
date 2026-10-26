from django.core.paginator import Paginator
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from taller_backend.utilidades import tiene_rol
from .models import Cliente
from .serializers import ClienteSerializer

#-----------------------------------------------------------------------------------------------

def respuesta_paginada(queryset, page_number):
    paginator = Paginator(queryset, 5)
    page = paginator.get_page(page_number)
    serializer = ClienteSerializer(page.object_list, many=True)
    return Response({
        'pagina_actual': page.number,
        'total_paginas': paginator.num_pages,
        'total_registros': paginator.count,
        'resultados': serializer.data
    })

#-----------------------------------------------------------------------------------------------

# Todos los usuarios pueden consultar clientes.
# Solo el administrador y la recepcionista pueden crear, modificar o eliminar.

@api_view(['GET', 'POST'])
def clientes_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        clientes = Cliente.objects.order_by('nombre')
        buscar = request.query_params.get('buscar')

        # Búsqueda parcial por nombre
        if buscar:
            clientes = clientes.filter(nombre__icontains=buscar)

        return respuesta_paginada(clientes, request.query_params.get('page', 1))

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ClienteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-----------------------------------------------------------------------------------------------

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def cliente_detalle_api(request, id):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        cliente = Cliente.objects.get(id=id)
    except Cliente.DoesNotExist:
        return Response({'error': 'Cliente no encontrado...'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ClienteSerializer(cliente).data)

    if not tiene_rol(request.user, ['Administrador', 'Recepcionista']):
        return Response({'detail': 'No tiene permiso para esta acción...'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        serializer = ClienteSerializer(
            cliente, data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Si el cliente tiene vehículos, Django no lo deja borrar (on_delete=PROTECT)
    # y lanza ProtectedError. En ese caso respondemos 409.
    try:
        cliente.delete()
    except ProtectedError:
        return Response({'error': 'No se puede eliminar el cliente porque tiene vehículos...'}, status=status.HTTP_409_CONFLICT)

    return Response(status=status.HTTP_204_NO_CONTENT)

#-----------------------------------------------------------------------------------------------

# Muestra el usuario que inició sesión y su rol

@api_view(['GET'])
def perfil_api(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Debe iniciar sesión...'}, status=status.HTTP_401_UNAUTHORIZED)

    grupo = request.user.groups.first()
    if grupo:
        rol = grupo.name
    else:
        rol = 'Sin rol'

    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'rol': rol
    })

#-----------------------------------------------------------------------------------------------
