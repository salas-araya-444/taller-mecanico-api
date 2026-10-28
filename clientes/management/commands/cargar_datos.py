from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from clientes.models import Cliente
from repuestos.models import Repuesto
from vehiculos.models import Vehiculo


# Comando para cargar datos de prueba:  python manage.py cargar_datos

# Django busca una clase llamada Command y ejecuta su método handle.
# Los parámetros *args y **options los pide Django, aunque aquí no se usan.

class Command(BaseCommand):
    help = 'Crea los roles, usuarios de prueba y algunos datos ficticios'

    def handle(self, *args, **options):
        if User.objects.filter(username='admin_taller').exists():
            self.stdout.write('Los datos de prueba ya estaban cargados.')
            return

        # Roles (grupos de Django)
        administrador = Group.objects.create(name='Administrador')
        recepcionista = Group.objects.create(name='Recepcionista')
        mecanico = Group.objects.create(name='Mecanico')

        # Usuarios de prueba (contraseña: Taller2026*)
        usuario = User.objects.create_user('admin_taller', password='Taller2026*', is_staff=True)
        usuario.groups.add(administrador)

        usuario = User.objects.create_user('recepcion', password='Taller2026*')
        usuario.groups.add(recepcionista)

        usuario = User.objects.create_user('mecanico1', password='Taller2026*')
        usuario.groups.add(mecanico)

        usuario = User.objects.create_user('mecanico2', password='Taller2026*')
        usuario.groups.add(mecanico)

        # Clientes y vehículos ficticios
        cliente1 = Cliente.objects.create(nombre='Ana Mora', cedula='601110222', telefono='88001122', correo='ana@ejemplo.com')
        cliente2 = Cliente.objects.create(nombre='Luis Soto', cedula='602220333', telefono='87002233', correo='luis@ejemplo.com')
        cliente3 = Cliente.objects.create(nombre='Carla Vega', cedula='603330444', telefono='86003344', correo='carla@ejemplo.com')

        Vehiculo.objects.create(cliente=cliente1, placa='ABC123', marca='Toyota', modelo='Corolla', anio=2015, kilometraje=120000)
        Vehiculo.objects.create(cliente=cliente1, placa='XYZ789', marca='Hyundai', modelo='Tucson', anio=2019, kilometraje=60000)
        Vehiculo.objects.create(cliente=cliente2, placa='BCD456', marca='Nissan', modelo='Sentra', anio=2012, kilometraje=180000)
        Vehiculo.objects.create(cliente=cliente3, placa='CDE234', marca='Toyota', modelo='Hilux', anio=2020, kilometraje=40000)

        # Repuestos del inventario
        Repuesto.objects.create(codigo='R001', nombre='Pastillas de freno', precio=18000, stock=20, stock_minimo=5)
        Repuesto.objects.create(codigo='R002', nombre='Aceite de motor', precio=6500, stock=30, stock_minimo=10)
        Repuesto.objects.create(codigo='R003', nombre='Filtro de aceite', precio=4500, stock=15, stock_minimo=5)
        Repuesto.objects.create(codigo='R004', nombre='Bujia', precio=5000, stock=3, stock_minimo=5)
        Repuesto.objects.create(codigo='R005', nombre='Bateria', precio=60000, stock=4, stock_minimo=2)

        self.stdout.write('Datos de prueba cargados correctamente.')
