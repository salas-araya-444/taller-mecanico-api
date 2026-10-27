from django.urls import path
from . import views

urlpatterns = [
    path('', views.facturas_api, name='facturas_api'),

    path('<int:id>/', views.factura_detalle_api, name='factura_detalle_api'),
]
