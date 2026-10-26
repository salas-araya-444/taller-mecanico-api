# Funciones para revisar el rol del usuario.
# Los roles son grupos de Django: Administrador, Recepcionista y Mecanico.


# Devuelve True si el usuario pertenece a alguno de los roles de la lista.
# El superusuario puede hacer todo.
def tiene_rol(usuario, roles):
    if usuario.is_superuser:
        return True
    return usuario.groups.filter(name__in=roles).exists()


# Devuelve True si el usuario es mecánico
def es_mecanico(usuario):
    return usuario.groups.filter(name='Mecanico').exists()
