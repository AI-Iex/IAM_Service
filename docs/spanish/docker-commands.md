# Docker Commands - Guía Rápida

## 🎯 Conceptos Clave: Profiles

Este proyecto usa **Docker Compose Profiles** para separar contextos:

| Profile | Cuándo usar | Servicios | DBs usadas |
|---------|-------------|----------|------------|
| **Ninguno (default)** | Desarrollo con DB externa (pgAdmin4/AWS RDS/Azure) | migrate, create_superuser, web | Tu DB externa |
| `--profile with-db` | Desarrollo con DB interna (Docker) | db, migrate, create_superuser, web | `iam_db` (dev) |
| `--profile test` | Tests (siempre DB aislada) | db_test, tests | `iam_db_test` (tests) |

### 🔑 Puntos Clave:

- **`db`** (dev interno) y **`db_test`** (tests) son containers **completamente separados**
- **NO comparten volúmenes** → `db_data` (dev) vs `db_test_data` (tests)
- Puedes correr dev interno + tests **simultáneamente sin conflictos**

**Ejemplos:**
```bash
# DB Externa (default) - Usa tu pgAdmin4/RDS/Azure
docker compose up

# DB Interna (dev) - Usa container 'db' (iam_db)
docker compose --profile with-db up

# Tests - Usa container 'db_test' (iam_db_test) AISLADO
docker compose --profile test run --rm tests
```

## 📊 Arquitectura de DBs: Resumen Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE DBs                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DB EXTERNA (pgAdmin4/AWS RDS/Azure)                        │
│  ├─ Container: Ninguno (fuera de Docker)                    │
│  ├─ Volumen: Gestionado externamente                        │
│  ├─ Profile: Ninguno (default)                              │
│  └─ Uso: Producción, desarrollo production-like             │
│                                                             │
│  DB INTERNA - DEV (iam_db)                                  │
│  ├─ Container: iam_db                                       │
│  ├─ Volumen: db_data (persistente)                          │
│  ├─ Profile: --profile with-db                              │
│  └─ Uso: Desarrollo sin servicios externos                  │
│                                                             │
│  DB INTERNA - TESTS (iam_db_test)                           │
│  ├─ Container: iam_db_test                                  │
│  ├─ Volumen: db_test_data (temporal)                        │
│  ├─ Profile: --profile test                                 │
│  └─ Uso: Tests aislados, CI/CD                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗑️ Limpiar y Eliminar

### Detener y eliminar containers (mantiene volúmenes/DB)
```bash
docker compose down
# Mantiene: db_data (dev), db_test_data (tests), es decir, no borra los datos de la db.
```

### Detener y eliminar TODO (incluye volúmenes de DBs internas)
```bash
# CUIDADO: Borra TODAS las DBs internas (dev + tests)
docker compose down -v

```

### Limpiar imágenes no usadas
```bash
docker system prune -f
```

### ⚠️ Limpiar TODO (imágenes, containers, volúmenes, redes)
```bash
docker system prune -a --volumes -f
# BORRA: Todas las imágenes, containers, volúmenes y redes
```

---

## 🏗️ Construir imagenes

### Build de todos los servicios (imagenes)
```bash
docker compose build
```

### Build de un servicio específico
```bash
docker compose build web
docker compose build migrate
docker compose build tests
```

### Build forzado (sin cache)
```bash
docker compose build --no-cache
```

---

## 🚀 Arrancar contenedores

### Desarrollo con DB Externa (pgAdmin4, AWS RDS, Supabase, Azure..)
```bash
docker compose up
# Levanta: migrate, create_superuser, web (NO levanta db)

```

### Desarrollo con DB Interna (Docker)
```bash
docker compose --profile with-db up
# Levanta: db, migrate, create_superuser, web
```

### Desarrollo en background (detached)
```bash
docker compose up -d
# o con DB interna:
docker compose --profile with-db up -d
```

### Producción (docker-compose.prod.yml)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Arrancar servicio específico
```bash
# Servicios de producción (funcionan con DB externa o interna)
docker compose up web
docker compose up migrate
docker compose up create_superuser

# DB dev interna (solo con profile)
docker compose --profile with-db up db

# DB tests (solo con profile)
docker compose --profile test up db_test
```

---

## 🔄 Recargar/Reiniciar

### Parar y continuar los servicios
```bash
# Parar
docker compose stop

# Iniciar de nuevo (rápido, usa los containers existentes)
docker compose start
```
### Reiniciar todos los servicios
```bash
docker compose restart
```

### Reiniciar un servicio específico
```bash
docker compose restart web
```

### Rebuild y reiniciar (cuando cambia código)
```bash
docker compose down
docker compose build
docker compose up -d

* El docker-compose.override.yml ya viene preparado para que el servicio web 
se auto-reinicie al guardar cambios en cualquier fichero .py.
```

### Rebuild y reiniciar (comando único)
```bash
docker compose up -d --build
```

---

## 🧪 Tests

### Correr todos los tests (levanta DB de tests automáticamente)
```bash
docker compose --profile test run --rm tests
```

### Correr tests específicos
```bash
docker compose --profile test run --rm -e PYTEST_ARGS="-k test_name -v" tests
```

### Correr tests con coverage
```bash
docker compose --profile test run --rm -e PYTEST_ARGS="--cov=app --cov-report=html" tests
```

### Limpiar después de tests
```bash
docker stop iam_db_test
docker rm iam_db_test
docker volume rm iam_service_db_test_data
```

### Tests + Dev simultáneos en consola de VS Code
```bash
# Terminal 1: Desarrollo con DB interna
docker compose --profile with-db up
# Usa: db (iam_db) + db_data volume

# Terminal 2: Tests (mientras dev corre)
docker compose --profile test run --rm tests
# Usa: db_test (iam_db_test) + db_test_data volume

```

---

## 🔧 Comandos Útiles

### Ver logs de un servicio
```bash
docker logs iam_web
docker logs iam_db
docker logs iam_migrate
```

### Ver logs en tiempo real (follow)
```bash
docker logs -f iam_web
```

### Ver estado de containers
```bash
docker compose ps
docker ps -a
```

### Ejecutar comando en container corriendo
```bash
docker exec -it iam_web bash
docker exec -it iam_db psql -U postgres -d IAMS_DB
```

### Ejecutar migraciones manualmente
```bash
docker compose run --rm migrate
```

### Crear superuser manualmente
```bash
docker compose run --rm create_superuser
```

---

## 🗄️ Base de Datos

### Conectar a PostgreSQL (DB Externa - pgAdmin4/RDS/Azure)
```bash
# Usa pgAdmin4 directamente o tu cliente PostgreSQL
# Host: localhost (o tu host externo)
# Port: 5432
# Database: IAMS_DB_External
```

### Conectar a PostgreSQL (DB Interna - Desarrollo)
```bash
# Solo si usas --profile with-db
docker exec -it iam_db psql -U postgres -d IAMS_DB
```

### Conectar a PostgreSQL (DB Tests)
```bash
# Solo cuando tests están corriendo
docker exec -it iam_db_test psql -U postgres -d IAMS_DB
```

### Ver tablas
```sql
\dt
```

### Ver versión de Alembic
```sql
SELECT * FROM alembic_version;
```

### Backup de la DB (Interna - Dev)
```bash
docker exec iam_db pg_dump -U postgres IAMS_DB > backup_dev.sql
```

### Backup de la DB (Externa)
```bash
# Desde pgAdmin4: Right-click DB → Backup
# O usando pg_dump local:
pg_dump -h localhost -U postgres -d IAMS_DB_External > backup_external.sql
```

### Restaurar DB (Interna - Dev)
```bash
docker exec -i iam_db psql -U postgres IAMS_DB < backup_dev.sql
```

### Restaurar DB (Externa)
```bash
psql -h localhost -U postgres -d IAMS_DB_External < backup_external.sql
```

### Salir/Desconectarse
```sql
\q
```
```bash
exit
```

---

## 🔄 Migraciones (Alembic)

### Ver historial de migraciones
```bash
docker compose run --rm web alembic history
```

### Ver versión actual
```bash
docker compose run --rm web alembic current
```

### Generar nueva migración automáticamente
```bash
docker compose run --rm web alembic revision --autogenerate -m "descripcion"
```

### Aplicar migraciones manualmente
```bash
docker compose run --rm web alembic upgrade head
```

### Hacer downgrade (volver 1 migración atrás)
```bash
docker compose run --rm web alembic downgrade -1
```

---

## 📋 Workflows Comunes

### Desarrollo: Empezar desde cero (DB Externa)
```bash
docker compose down -v
docker compose build
docker compose up  # migrate + superuser + web
```

### Desarrollo: Empezar desde cero (DB Interna)
```bash
docker compose --profile with-db down -v
docker compose --profile with-db build
docker compose --profile with-db up
```

### Desarrollo: Cambié código Python
```bash
# Hot reload automático con docker-compose.override.yml
# Solo guarda (Ctrl+S) y espera unos segundos

# Si no funciona:
docker compose restart web
```

### Desarrollo: Cambié un modelo (nueva columna, tabla, etc.)
```bash
# 1. Genera la migración
docker compose run --rm web alembic revision --autogenerate -m "add phone_number"

# 2. Revisa el archivo generado en alembic/versions/

# 3. Aplica la migración
docker compose down
docker compose up  # Ejecuta migrate automáticamente
```


### Producción: Deploy nueva versión
```bash
# En el servidor de producción:
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---


## 🆘 Troubleshooting

### Container no arranca
```bash
# Ver logs del container
docker logs iam_web

# Ver estado detallado
docker inspect iam_web
```

### DB no está healthy
```bash
# Ver logs de PostgreSQL
docker logs iam_db

# Verificar healthcheck
docker inspect iam_db --format='{{.State.Health.Status}}'
```

### Puerto ya en uso
```bash
# Ver qué proceso usa el puerto 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Cambiar puerto en .env
PORT=8001
```