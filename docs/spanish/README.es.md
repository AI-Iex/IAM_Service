# 🔐 IAM Service

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-170+-brightgreen.svg)](tests/)
[![Docker](https://img.shields.io/badge/docker-listo-blue.svg)](Dockerfile)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-purple.svg)](tools/)

> Un microservicio de Gestión de Identidad y Acceso (IAM) listo para producción, construido con FastAPI e implementando patrones de seguridad de nivel empresarial y principios modernos de arquitectura de software.

Español | **[English](../../README.md)**

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Características Principales](#-características-principales)
- [Arquitectura](#-arquitectura)
- [Stack Tecnológico](#-stack-tecnológico)
- [Primeros Pasos](#-primeros-pasos)
- [Documentación de la API](#-documentación-de-la-api)
- [Testing](#-testing)
- [Integración MCP](#-integración-mcp)
- [Contribuir](#-contribuir)

---

## 🌟 Descripción General

Este servicio IAM es una versión ligera y personal derivada de un proyecto profesional real. Proporciona una solución completa para la gestión de identidad y acceso, incluyendo autenticación de usuarios, autorización, control de acceso basado en roles (RBAC) y gestión de aplicaciones cliente.

### ¿Para qué sirve?

- **Autenticación de Microservicios**: Autenticación y autorización segura para sistemas distribuidos
- **Aplicaciones Multi-tenant**: Gestión de usuarios, roles y permisos a través de diferentes clientes
- **Seguridad de API Gateway**: Proveedor de identidad centralizado para ecosistemas de APIs
- **Aprendizaje y Experimentación**: Arquitectura limpia y bien documentada para estudiar patrones modernos de IAM

---

## ✨ Características Principales

### 🔒 Seguridad y Autenticación

- **Autenticación basada en JWT** con tokens de acceso y refresh
- **Hash Seguro de Contraseñas** usando Argon2 y bcrypt
- **Rotación de Refresh Tokens** con soporte para lista negra y multiplataforma
- **Autenticación Machine-to-Machine (M2M)** para aplicaciones cliente
- **Políticas de Contraseña** con reglas de negocio personalizables
- **Refresh Tokens basados en Cookies** con flags HTTP-only y secure

### 👥 Gestión de Usuarios

- **Registro de Usuarios Self-service** con validación de email
- **Creación de Usuarios por Administrador** con contraseñas temporales
- **Gestión de Perfiles de Usuario** (actualizar, activar/desactivar, eliminar)
- **Flujo de Cambio de Email** con confirmación de contraseña
- **Cambio de Contraseña** con validación de contraseña antigua
- **Forzar Cambio de Contraseña** en el primer inicio de sesión para usuarios creados por admin

### 🎭 Control de Acceso Basado en Roles (RBAC)

- **Sistema de Permisos Granular** con más de 16 permisos predefinidos
- **Gestión Dinámica de Roles** (crear, actualizar, eliminar roles)
- **Asignación Rol-Permiso** con composición flexible
- **Asignación Usuario-Rol** con soporte para múltiples roles
- **Soporte para Superusuario** para acceso administrativo
- **Guardas de Permisos** con protección basada en decoradores

### 🔌 Aplicaciones Cliente

- **Client Credentials Flow** (OAuth 2.0)
- **Asignación Cliente-Permiso** para acceso con alcance definido
- **Gestión de Secretos** con generación y hash seguro
- **Controles de Activación/Desactivación de Clientes**

### 🧪 Aseguramiento de Calidad

- **Más de 170 Tests Comprensivos**:
  - Tests unitarios para servicios y repositorios
  - Tests de integración para endpoints de la API
  - Tests end-to-end para flujos completos
  - Tests de seguridad para detección de vulnerabilidades
  - Tests de rendimiento para validación de carga
- **Más del 90% de Cobertura de Código**
- **Pipeline CI/CD Automatizado** con análisis de seguridad y código
- **Type Checking** con Pydantic v2
- **Linting y Formateo** con Ruff y Black

### 🤖 Herramientas de IA y Desarrollo

- **Compatible con MCP (Model Context Protocol)** para integración con LLMs
- **Múltiples Formatos de Exportación de Herramientas**: JSON, TOML, YAML, LangChain
- **Documentación OpenAPI/Swagger** con UI interactiva
- **Documentación ReDoc** para referencia detallada de la API

---

## 🏗️ Arquitectura

Este proyecto sigue los principios de **Domain-Driven Design (DDD)** y patrones modernos de arquitectura de software:

### Patrones de Diseño y Principios

#### 🎯 Patrones Principales

- **Patrón Repository**: Capa de abstracción para la lógica de acceso a datos
- **Patrón Service Layer**: Encapsulación y orquestación de lógica de negocio
- **Patrón Unit of Work**: Gestión de transacciones a través de múltiples repositorios
- **Inyección de Dependencias**: Bajo acoplamiento y testabilidad con el sistema de dependencias de FastAPI
- **Patrón Strategy**: Selección flexible de algoritmo de hash de contraseñas
- **Patrón Factory**: Creación dinámica de objetos (tokens, sesiones)

#### 🧱 Capas Arquitectónicas

```
┌─────────────────────────────────────────┐
│        Capa API (Routes)                │
│  ┌─────────────────────────────────┐    │
│  │    Endpoints FastAPI & DTOs     │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     Middleware & Dependencias           │
│  ┌─────────────────────────────────┐    │
│  │  Auth, Logging, Context, CORS   │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Capa de Servicio (Business)        │
│  ┌─────────────────────────────────┐    │
│  │  Lógica de Negocio & Validación │    │
│  │   UserService, AuthService...   │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    Capa Repository (Acceso a Datos)     │
│  ┌─────────────────────────────────┐    │
│  │  Operaciones CRUD & Queries     │    │
│  │  UserRepo, RoleRepo...          │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Capa de Base de Datos (ORM)       │
│  ┌─────────────────────────────────┐    │
│  │  Modelos SQLAlchemy & Esquemas  │    │
│  │  Base de Datos PostgreSQL       │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

#### 📂 Estructura del Proyecto

```
IAM_Service/
├── app/
│   ├── api/              # Rutas y endpoints de la API
│   ├── services/         # Capa de lógica de negocio
│   ├── repositories/     # Capa de acceso a datos
│   ├── models/           # Modelos ORM de SQLAlchemy
│   ├── schemas/          # DTOs de Pydantic
│   ├── core/             # Configuraciones centrales y seguridad
│   ├── db/               # Sesión de base de datos y UoW
│   ├── middleware/       # Middleware de request/response
│   └── dependencies/     # Dependencias de FastAPI
├── tests/                # Suite de tests comprensiva
├── alembic/              # Migraciones de base de datos
├── scripts/              # Scripts de utilidad
├── tools/                # Exportación de herramientas MCP
└── docs/                 # Documentación
```

---

## 🛠️ Stack Tecnológico

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno y de alto rendimiento
- **[Python 3.12+](https://www.python.org/)** - Últimas características y rendimiento de Python
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** - ORM async 
- **[Pydantic v2](https://docs.pydantic.dev/)** - Validación de datos
- **[Alembic](https://alembic.sqlalchemy.org/)** - Herramienta de migración de base de datos

### Base de Datos

- **[PostgreSQL 15+](https://www.postgresql.org/)** - Base de datos relacional

### Seguridad

- **[python-jose](https://github.com/mpdavis/python-jose)** - Implementación JWT
- **[passlib](https://passlib.readthedocs.io/)** - Hash de contraseñas (Argon2, bcrypt)
- **[python-multipart](https://github.com/andrew-d/python-multipart)** - Análisis de datos de formulario

### Testing

- **[pytest](https://pytest.org/)** - Framework de testing
- **[pytest-asyncio](https://pytest-asyncio.readthedocs.io/)** - Soporte para tests async
- **[pytest-cov](https://pytest-cov.readthedocs.io/)** - Reportes de cobertura
- **[httpx](https://www.python-httpx.org/)** - Cliente HTTP async para testing

### DevOps

- **[Docker](https://www.docker.com/)** - Contenedorización
- **[Docker Compose](https://docs.docker.com/compose/)** - Orquestación multi-contenedor
- **[Gunicorn](https://gunicorn.org/)** - Servidor HTTP WSGI
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI

### Calidad de Código

- **[Ruff](https://github.com/astral-sh/ruff)** - Linter rápido de Python
- **[Black](https://black.readthedocs.io/)** - Formateador de código

---

## 🚀 Primeros Pasos

### Prerrequisitos

- **Docker & Docker Compose** (recomendado)
- **Python 3.12+** (para desarrollo local)
- **PostgreSQL 15+** (si se ejecuta sin Docker)

### Inicio Rápido con Docker

1. **Clonar el repositorio**

```bash
git clone https://github.com/AI-Iex/IAM_Service.git
cd IAM_Service
```

2. **Crear archivo de entorno**

```bash
cp .env.example .env
```

Editar `.env` con tu configuración:

```env
# Configuración del Servicio
SERVICE_NAME=IAM Service
SERVICE_VERSION=1
SERVICE_DESCRIPTION=Identity and Access Management Service
SERVICE_LICENSE=MIT

# Base de Datos
DATABASE_URL=postgresql+asyncpg://iam_user:password@db:5432/iam_db
TEST_DATABASE_URL=postgresql+asyncpg://iam_user:password@db_test:5432/iam_db_test

# Seguridad
JWT_SECRET_KEY=tu-super-secreto-jwt-key-cambia-esto
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_SECRET=tu-super-secreto-refresh-key-cambia-esto
REFRESH_TOKEN_EXPIRE_DAYS=7

# Superusuario (se creará en el primer inicio si está habilitado)
CREATE_SUPERUSER_ON_STARTUP=true
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=CambiaEstaContraseña123!
SUPERUSER_NAME=Usuario Admin

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Rutas
SERVICE_PERMISSIONS_PATH=app/config/permissions_map.json
BUSINESS_RULES_PATH=app/config/business_rules.json
LOGGING_CONFIG_PATH=app/config/log_schema.json
```

3. **Iniciar los servicios**

```bash
# Iniciar con base de datos (desarrollo)
docker-compose --profile with-db up -d

# O iniciar solo la API (si tienes BD externa)
docker-compose up -d
```

4. **Ejecutar migraciones y poblar datos**

```bash
docker-compose exec app python scripts/migrate_and_seed.py
```

5. **Acceder a la aplicación**

- **Documentación API (Swagger)**: http://localhost:8000/docs
- **Documentación API (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### Configuración de Desarrollo Local

1. **Crear entorno virtual**

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

2. **Instalar dependencias**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Configurar base de datos**

```bash
# Iniciar PostgreSQL con Docker
docker-compose --profile with-db up -d db

# Ejecutar migraciones
alembic upgrade head

# Poblar datos iniciales
python scripts/migrate_and_seed.py
```

4. **Ejecutar la aplicación**

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📚 Documentación de la API

### Endpoints Disponibles

#### 🔐 Autenticación (`/api/v1/auth`)

- `POST /auth` - Registrar nuevo usuario
- `POST /auth/login` - Iniciar sesión y obtener tokens
- `POST /auth/refresh` - Refrescar token de acceso
- `POST /auth/logout` - Cerrar sesión e invalidar token
- `POST /auth/logout_all_devices` - Cerrar sesión e invalidar todos los tokens
- `POST /auth/client` - Autenticación de credenciales de cliente

#### 👥 Usuarios (`/api/v1/users`)

- `POST /users` - Crear usuario (admin)
- `GET /users` - Listar usuarios con filtros
- `GET /users/me` - Obtener perfil del ususario actual
- `GET /users/{user_id}` - Obtener usuario por ID
- `PATCH /users/{user_id}` - Actualizar usuario
- `DELETE /users/{user_id}` - Eliminar usuario
- `PUT /users/{user_id}/email` - Cambiar email de usuario
- `PUT /users/{user_id}/password` - Cambiar contraseña de usuario
- `POST /users/{user_id}/roles/{role_id}` - Asignar rol a usuario
- `DELETE /users/{user_id}/roles/{role_id}` - Quitar rol de usuario

#### 🎭 Roles (`/api/v1/roles`)

- `POST /roles` - Crear rol
- `GET /roles` - Listar roles con filtros
- `GET /roles/{role_id}` - Obtener rol por ID
- `PATCH /roles/{role_id}` - Actualizar rol
- `DELETE /roles/{role_id}` - Eliminar rol
- `POST `/roles/{role_id}/permissions/{permission_id}` - Asignar permiso a rol
- `DELETE `/roles/{role_id}/permissions/{permission_id}` - Quitar permiso a rol

#### 🔑 Permisos (`/api/v1/permissions`)

- `POST /permissions` - Crear permiso
- `GET /permissions` - Listar permisos con filtros
- `GET /permissions/{permission_id}` - Obtener permiso por ID
- `PATCH /permissions/{permission_id}` - Actualizar permiso
- `DELETE /permissions/{permission_id}` - Eliminar permiso

#### 🔌 Clientes (`/api/v1/clients`)

- `POST /clients` - Crear aplicación cliente
- `GET /clients` - Listar clientes con filtros
- `GET /clients/me` - Obtener perfil del cliente actual
- `GET /clients/{client_id}` - Obtener cliente por ID
- `PATCH /clients/{client_id}` - Actualizar cliente
- `DELETE /clients/{client_id}` - Eliminar cliente
- `POST /clients/{client_id}/permissions` - Asignar permisos a cliente
- `DELETE /clients/{client_id}/permissions` - Quitar permisos de cliente

#### ❤️ Salud (`/api/v1/health`)

- `GET /health` - Endpoint de comprobación de salud

### Documentación Interactiva

Una vez que el servicio esté ejecutándose, visita:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Testing

### Ejecutar Todos los Tests

```bash
# Con reporte de cobertura
pytest --cov=app --cov-report=html --cov-report=term

# Categoría específica de tests
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/security/
pytest tests/performance/
```

### Estructura de Tests

```
tests/
├── unit/                 # Tests unitarios para servicios, repositorios
├── integration/          # Tests de integración para endpoints de API
├── e2e/                  # Tests end-to-end de flujos completos
├── security/             # Tests de vulnerabilidades de seguridad
├── performance/          # Tests de carga y rendimiento
└── conftest.py           # Fixtures y configuración de tests
```

### Reporte de Cobertura

Después de ejecutar los tests con cobertura, abre `htmlcov/index.html` en tu navegador para ver reportes detallados de cobertura.

---

## 🤖 Integración MCP

Este servicio es compatible con el **Model Context Protocol (MCP)**, permitiendo integración fluida con Modelos de Lenguaje Grande (LLMs) para gestión de identidad potenciada por IA.

### Generar Herramientas MCP

```bash
# Generar todos los formatos
python scripts/tools_generator.py

# Generar formato específico
python scripts/tools_generator.py --format toml
python scripts/tools_generator.py --format langchain
python scripts/tools_generator.py --format json
```

### Formatos de Herramientas Disponibles

- **JSON** (`tools/iam_tools.json`) - Formato MCP estándar
- **TOML** (`tools/iam_tools.toml`) - Configuración TOML
- **YAML** (`tools/iam_tools.yaml`) - Configuración YAML
- **LangChain** (`tools/iam_tools_langchain.json`) - Integración con LangChain
- **MCP Nativo** (`tools/iam_tools_mcp.json`) - Formato MCP nativo

### Casos de Uso con LLMs

- **Aprovisionamiento Automatizado de Usuarios**: "Crea un nuevo usuario con rol de editor"
- **Gestión de Acceso**: "Otorga permisos de lectura al rol de analítica"
- **Consultas de Auditoría**: "Lista todos los usuarios con privilegios de admin"
- **Revisiones de Seguridad**: "Muestra todos los permisos asignados a este cliente"

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Este proyecto está abierto a mejoras, corrección de bugs y adición de características.

### Cómo Contribuir

1. **Hacer fork del repositorio**
2. **Crear una rama de característica** (`git checkout -b feature/caracteristica-increible`)
3. **Hacer commit de tus cambios** (`git commit -m 'Añadir característica increíble'`)
4. **Push a la rama** (`git push origin feature/caracteristica-increible`)
5. **Abrir un Pull Request**

### Guías de Desarrollo

- Seguir el estilo de código existente (Ruff + Black)
- Escribir tests para nuevas características
- Actualizar documentación según sea necesario
- Asegurar que todos los tests pasen antes de enviar PR
- Mantener commits atómicos y bien descritos

### Reportar Issues

¿Encontraste un bug o tienes una sugerencia? Por favor [abre un issue](https://github.com/AI-Iex/IAM_Service/issues) con:

- Descripción clara del problema/sugerencia
- Pasos para reproducir (para bugs)
- Comportamiento esperado vs comportamiento actual
- Detalles del entorno (SO, versión de Python, etc.)

---

## 📧 Contacto

**Alejandro Sastre**

- Email: alexsastre099@gmail.com
- GitHub: [@AI-Iex](https://github.com/AI-Iex)

---

<div align="center">

**[⬆ Volver Arriba](#-iam-service)**

Por [Alejandro Sastre](https://github.com/AI-Iex)

</div>
