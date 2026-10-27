from django.urls import path
from . import views

urlpatterns = [
    path('', views.ordenes_api, name='ordenes_api'),

    path('<int:id>/', views.orden_detalle_api, name='orden_detalle_api'),

    path('<int:id>/cambiar-estado/', views.cambiar_estado_api, name='cambiar_estado_api'),

    path('<int:id>/detalles/', views.detalles_orden_api, name='detalles_orden_api'),

    path('detalles/<int:id>/', views.detalle_api, name='detalle_api'),
]
