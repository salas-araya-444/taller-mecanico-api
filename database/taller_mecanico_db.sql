-- Prepara la base de datos y el usuario de MySQL para el proyecto.
-- Ejecutar como root (MySQL Workbench o la consola de MySQL).
-- Antes de ejecutar: cambie CAMBIAR_POR_CONTRASENA_LOCAL por su propia contraseña
-- y use la misma en DB_PASSWORD del archivo .env

CREATE DATABASE IF NOT EXISTS taller_mecanico_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

SHOW DATABASES;

CREATE USER IF NOT EXISTS 'taller_user'@'localhost'
IDENTIFIED BY 'CAMBIAR_POR_CONTRASENA_LOCAL';

GRANT ALL PRIVILEGES
ON taller_mecanico_db.*
TO 'taller_user'@'localhost';

-- Permiso para la base temporal que Django crea al ejecutar las pruebas automatizadas
GRANT ALL PRIVILEGES
ON test_taller_mecanico_db.*
TO 'taller_user'@'localhost';

FLUSH PRIVILEGES;

SHOW GRANTS FOR 'taller_user'@'localhost';
