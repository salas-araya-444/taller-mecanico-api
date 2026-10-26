from django.urls import path
from . import views

urlpatterns = [
    path('', views.repuestos_api, name='repuestos_api'),

    path('<int:id>/', views.repuesto_detalle_api, name='repuesto_detalle_api'),
]
