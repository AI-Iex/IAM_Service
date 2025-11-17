# 🔐 IAM Service (Identity and Access Management)

Sistema de gestión de identidades, autenticación y autorización construido con FastAPI, PostgreSQL y Docker.

---

## 📖 Documentación

**¿Primera vez usando este proyecto?** Lee estas guías en orden:

1. **[README-DOCKER.md](./docs/README-DOCKER.md)** - 🚀 Guía completa para principiantes
   - Qué es el proyecto y cómo funciona
   - Estructura de archivos (cuáles usar, cuáles ignorar)
   - Configuración paso a paso
   - Desarrollo vs Producción
   - Solución de problemas

2. **[docker-commands.md](./docs/docker-commands.md)** - 🐋 Comandos Docker esenciales
   - Comandos de limpieza y build
   - Arrancar y recargar servicios
   - Correr tests
   - Migraciones y DB
   - Workflows comunes

3. **[.env.example](./.env.example)** - ⚙️ Plantilla de configuración
   - Variables de entorno necesarias
   - Valores de ejemplo
   - Notas de seguridad

---

## ⚡ Inicio Rápido

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Editar .env con tus configuraciones
# (al menos cambiar SECRET_KEY y passwords)

# 3. Iniciar todo con Docker
make up
# O sin Makefile:
docker compose up --build

# 4. Esperar a que termine (verás logs)
# Cuando veas "Listening at: http://0.0.0.0:8000" está listo

# 5. Abrir en el navegador
# http://localhost:8000/docs
```

**¡Listo!** La API está corriendo con:
- ✅ Base de datos PostgreSQL
- ✅ 16 permisos sembrados
- ✅ Rol admin creado
- ✅ Usuario admin (admin@gmail.com)
- ✅ 173 tests ejecutados
- ✅ API en http://localhost:8000

---

## 🏗️ Arquitectura

### Stack Tecnológico

- **Backend**: FastAPI (Python 3.12)
- **Base de Datos**: PostgreSQL 15 (Alpine)
- **Autenticación**: JWT (JSON Web Tokens)
- **Testing**: Pytest (173 tests)
- **Containerización**: Docker + Docker Compose
- **ASGI Server**: Gunicorn + Uvicorn

### Flujo de Servicios

```
db → migrate → create_superuser → tests → web
```

Todos los pasos son secuenciales y orquestados con Docker Compose.

---

## 📂 Estructura del Proyecto

```
IAM_Service
├─ .pytest_cache
│  ├─ CACHEDIR.TAG
│  └─ v
│     └─ cache
│        ├─ lastfailed
│        └─ nodeids
├─ app
│  ├─ api
│  │  ├─ routes
│  │  │  ├─ auth.py
│  │  │  ├─ client.py
│  │  │  ├─ health.py
│  │  │  ├─ permission.py
│  │  │  ├─ role.py
│  │  │  └─ user.py
│  │  └─ __init__.py
│  ├─ assets
│  │  ├─ icons
│  │  └─ images
│  ├─ config
│  │  ├─ business_rules.json
│  │  ├─ log_schema.json
│  │  └─ permissions_map.json
│  ├─ core
│  │  ├─ business_config.py
│  │  ├─ config.py
│  │  ├─ exceptions.py
│  │  ├─ logging_config.py
│  │  ├─ permissions.py
│  │  ├─ permissions_loader.py
│  │  ├─ security.py
│  │  └─ __init__.py
│  ├─ db
│  │  ├─ base.py
│  │  ├─ bootstrap.py
│  │  ├─ interfaces
│  │  │  └─ unit_of_work.py
│  │  ├─ session.py
│  │  ├─ unit_of_work.py
│  │  └─ __init__.py
│  ├─ dependencies
│  │  ├─ auth.py
│  │  ├─ services.py
│  │  └─ __init__.py
│  ├─ kafka
│  ├─ main.py
│  ├─ middleware
│  │  ├─ auth_context.py
│  │  ├─ context.py
│  │  ├─ exception_handler.py
│  │  ├─ logging.py
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ client.py
│  │  ├─ client_permission.py
│  │  ├─ permission.py
│  │  ├─ refresh_token.py
│  │  ├─ role.py
│  │  ├─ role_permission.py
│  │  ├─ user.py
│  │  ├─ user_role.py
│  │  └─ __init__.py
│  ├─ repositories
│  │  ├─ auth.py
│  │  ├─ client.py
│  │  ├─ health.py
│  │  ├─ interfaces
│  │  │  ├─ auth.py
│  │  │  ├─ client.py
│  │  │  ├─ health.py
│  │  │  ├─ permission.py
│  │  │  ├─ refresh_token.py
│  │  │  ├─ role.py
│  │  │  └─ user.py
│  │  ├─ permission.py
│  │  ├─ refresh_token.py
│  │  ├─ role.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ schemas
│  │  ├─ auth.py
│  │  ├─ client.py
│  │  ├─ health.py
│  │  ├─ permission.py
│  │  ├─ role.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ auth.py
│  │  ├─ client.py
│  │  ├─ health.py
│  │  ├─ interfaces
│  │  │  ├─ auth.py
│  │  │  ├─ client.py
│  │  │  ├─ health.py
│  │  │  ├─ permission.py
│  │  │  ├─ role.py
│  │  │  ├─ user.py
│  │  │  └─ __init__.py
│  │  ├─ permission.py
│  │  ├─ role.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ Dockerfile
├─ docker_compose.yml
├─ permissions_map.json
├─ pytest.ini
├─ requirements.txt
└─ tests
   ├─ conftest.py
   ├─ connection
   │  └─ test_connection.py
   ├─ e2e
   │  └─ test_full_user_role_permission_flow.py
   ├─ integration
   │  └─ api
   │     ├─ test_auth_routes.py
   │     ├─ test_clients_routes.py
   │     ├─ test_permissions_routes.py
   │     ├─ test_roles_routes.py
   │     └─ test_users_routes.py
   ├─ performance
   │  ├─ test_database_query_latency.py
   │  └─ test_password_hashing_speed.py
   ├─ security
   │  ├─ test_hash_passwords.py
   │  └─ test_jwt_generation_and_validation.py
   ├─ unit
   │  ├─ core
   │  │  ├─ test_config.py
   │  │  ├─ test_exceptions.py
   │  │  ├─ test_logging_config.py
   │  │  └─ test_permissions_loader.py
   │  ├─ db
   │  │  ├─ test_bootstrap.py
   │  │  ├─ test_session.py
   │  │  └─ test_unit_of_work.py
   │  ├─ middleware
   │  │  ├─ test_context.py
   │  │  └─ test_exception_handler.py
   │  ├─ repositories
   │  │  ├─ test_auth_repository.py
   │  │  ├─ test_client_repository.py
   │  │  ├─ test_permission_repository.py
   │  │  ├─ test_refresh_token_repository.py
   │  │  ├─ test_role_repository.py
   │  │  └─ test_user_repository.py
   │  └─ services
   │     ├─ test_auth_service.py
   │     ├─ test_client_service.py
   │     ├─ test_permission_service.py
   │     ├─ test_role_service.py
   │     └─ test_user_service.py
   └─ __init__.py

```