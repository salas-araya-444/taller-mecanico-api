from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from clientes.views import perfil_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', obtain_auth_token, name='api-token'),
    path('api/perfil/', perfil_api, name='perfil_api'),

    path('api/clientes/', include('clientes.urls')),
]
