from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehiculos_api, name='vehiculos_api'),

    path('<int:id>/', views.vehiculo_detalle_api, name='vehiculo_detalle_api'),

    path('<int:id>/historial/', views.historial_vehiculo_api, name='historial_vehiculo_api'),
]
