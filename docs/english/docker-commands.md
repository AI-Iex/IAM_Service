# Docker Commands - Quick Guide

## 🎯 Key Concepts: Profiles

This project uses **Docker Compose Profiles** to separate contexts:

| Profile | When to use | Services | DBs used |
|---------|-------------|----------|----------|
| **None (default)** | Development with external DB (pgAdmin4/AWS RDS/Azure) | migrate, create_superuser, web | Your external DB |
| `--profile with-db` | Development with internal DB (Docker) | db, migrate, create_superuser, web | `iam_db` (dev) |
| `--profile test` | Tests (always isolated DB) | db_test, tests | `iam_db_test` (tests) |

### 🔑 Key Points:

- **`db`** (internal dev) and **`db_test`** (tests) are **completely separate** containers
- **DO NOT share volumes** → `db_data` (dev) vs `db_test_data` (tests)
- You can run internal dev + tests **simultaneously without conflicts**
- `docker compose --profile test down -v` **ONLY deletes `db_test`**, does NOT affect `db` or `web`

**Examples:**
```bash
# External DB (default) - Uses your pgAdmin4/RDS/Azure
docker compose up

# Internal DB (dev) - Uses container 'db' (iam_db)
docker compose --profile with-db up

# Tests - Uses container 'db_test' (iam_db_test) ISOLATED
docker compose --profile test run --rm tests
```

## 📊 DB Architecture: Visual Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DB ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL DB (pgAdmin4/AWS RDS/Azure)                       │
│  ├─ Container: None (outside Docker)                        │
│  ├─ Volume: Managed externally                              │
│  ├─ Profile: None (default)                                 │
│  └─ Usage: Production, production-like development          │
│                                                             │
│  INTERNAL DB - DEV (iam_db)                                 │
│  ├─ Container: iam_db                                       │
│  ├─ Volume: db_data (persistent)                            │
│  ├─ Profile: --profile with-db                              │
│  └─ Usage: Development without external services            │
│                                                             │
│  INTERNAL DB - TESTS (iam_db_test)                          │
│  ├─ Container: iam_db_test                                  │
│  ├─ Volume: db_test_data (temporary)                        │
│  ├─ Profile: --profile test                                 │
│  └─ Usage: Isolated tests, CI/CD                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗑️ Clean and Remove

### Stop and remove containers (keeps volumes/DB)
```bash
docker compose down
# Keeps: db_data (dev), db_test_data (tests), i.e., does not delete DB data
```

### Stop and remove EVERYTHING (includes internal DB volumes)
```bash
# CAUTION: Deletes ALL internal DBs (dev + tests)
docker compose down -v
```

### Clean unused images
```bash
docker system prune -f
```

### ⚠️ Clean EVERYTHING (images, containers, volumes, networks)
```bash
docker system prune -a --volumes -f
# DELETES: All images, containers, volumes and networks
```

---

## 🏗️ Build Images

### Build all services (images)
```bash
docker compose build
```

### Build specific service
```bash
docker compose build web
docker compose build migrate
docker compose build tests
```

### Forced build (no cache)
```bash
docker compose build --no-cache
```

---

## 🚀 Start Containers

### Development with External DB (pgAdmin4, AWS RDS, Supabase, Azure..)
```bash
docker compose up
# Starts: migrate, create_superuser, web (does NOT start db)
```

### Development with Internal DB (Docker)
```bash
docker compose --profile with-db up
# Starts: db, migrate, create_superuser, web
```

### Development in background (detached)
```bash
docker compose up -d
# or with internal DB:
docker compose --profile with-db up -d
```

### Production (docker-compose.prod.yml)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Start specific service
```bash
# Production services (work with external or internal DB)
docker compose up web
docker compose up migrate
docker compose up create_superuser

# Internal dev DB (only with profile)
docker compose --profile with-db up db

# Test DB (only with profile)
docker compose --profile test up db_test
```

---

## 🔄 Reload/Restart

### Stop and resume services
```bash
# Stop
docker compose stop

# Start again (fast, uses existing containers)
docker compose start
```

### Restart all services
```bash
docker compose restart
```

### Restart specific service
```bash
docker compose restart web
```

### Rebuild and restart (when code changes)
```bash
docker compose down
docker compose build
docker compose up -d

* The docker-compose.override.yml is already configured so the web service
auto-restarts when saving changes to any .py file.
```

### Rebuild and restart (single command)
```bash
docker compose up -d --build
```

---

## 🧪 Tests

### Run all tests (automatically starts test DB)
```bash
docker compose --profile test run --rm tests
```

### Run specific tests
```bash
docker compose --profile test run --rm -e PYTEST_ARGS="-k test_name -v" tests
```

### Run tests with coverage
```bash
docker compose --profile test run --rm -e PYTEST_ARGS="--cov=app --cov-report=html" tests
```

### Cleanup after tests
```bash
docker stop iam_db_test
docker rm iam_db_test
docker volume rm iam_service_db_test_data
```

### Tests + Dev simultaneously in VS Code console
```bash
# Terminal 1: Development with internal DB
docker compose --profile with-db up
# Uses: db (iam_db) + db_data volume

# Terminal 2: Tests (while dev is running)
docker compose --profile test run --rm tests
# Uses: db_test (iam_db_test) + db_test_data volume
```

---

## 🔧 Useful Commands

### View service logs
```bash
docker logs iam_web
docker logs iam_db
docker logs iam_migrate
```

### View logs in real-time (follow)
```bash
docker logs -f iam_web
```

### View container status
```bash
docker compose ps
docker ps -a
```

### Execute command in running container
```bash
docker exec -it iam_web bash
docker exec -it iam_db psql -U postgres -d IAMS_DB
```

### Execute migrations manually
```bash
docker compose run --rm migrate
```

### Create superuser manually
```bash
docker compose run --rm create_superuser
```

---

## 🗄️ Database

### Connect to PostgreSQL (External DB - pgAdmin4/RDS/Azure)
```bash
# Use pgAdmin4 directly or your PostgreSQL client
# Host: localhost (or your external host)
# Port: 5432
# Database: IAMS_DB_External
```

### Connect to PostgreSQL (Internal DB - Development)
```bash
# Only if using --profile with-db
docker exec -it iam_db psql -U postgres -d IAMS_DB
```

### Connect to PostgreSQL (Test DB)
```bash
# Only when tests are running
docker exec -it iam_db_test psql -U postgres -d IAMS_DB
```

### View tables
```sql
\dt
```

### View Alembic version
```sql
SELECT * FROM alembic_version;
```

### Backup DB (Internal - Dev)
```bash
docker exec iam_db pg_dump -U postgres IAMS_DB > backup_dev.sql
```

### Backup DB (External)
```bash
# From pgAdmin4: Right-click DB → Backup
# Or using local pg_dump:
pg_dump -h localhost -U postgres -d IAMS_DB_External > backup_external.sql
```

### Restore DB (Internal - Dev)
```bash
docker exec -i iam_db psql -U postgres IAMS_DB < backup_dev.sql
```

### Restore DB (External)
```bash
psql -h localhost -U postgres -d IAMS_DB_External < backup_external.sql
```

### Exit/Disconnect
```sql
\q
```
```bash
exit
```

---

## 🔄 Migrations (Alembic)

### View migration history
```bash
docker compose run --rm web alembic history
```

### View current version
```bash
docker compose run --rm web alembic current
```

### Generate new migration automatically
```bash
docker compose run --rm web alembic revision --autogenerate -m "description"
```

### Apply migrations manually
```bash
docker compose run --rm web alembic upgrade head
```

### Downgrade (go back 1 migration)
```bash
docker compose run --rm web alembic downgrade -1
```

---

## 📋 Common Workflows

### Development: Start from scratch (External DB)
```bash
docker compose down -v
docker compose build
docker compose up  # migrate + superuser + web
```

### Development: Start from scratch (Internal DB)
```bash
docker compose --profile with-db down -v
docker compose --profile with-db build
docker compose --profile with-db up
```

### Development: Changed Python code
```bash
# Automatic hot reload with docker-compose.override.yml
# Just save (Ctrl+S) and wait a few seconds

# If it doesn't work:
docker compose restart web
```

### Development: Changed a model (new column, table, etc.)
```bash
# 1. Generate migration
docker compose run --rm web alembic revision --autogenerate -m "add phone_number"

# 2. Review generated file in alembic/versions/

# 3. Apply migration
docker compose down
docker compose up  # Executes migrate automatically
```

### Production: Deploy new version
```bash
# On production server:
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 🆘 Troubleshooting

### Container won't start
```bash
# View container logs
docker logs iam_web

# View detailed status
docker inspect iam_web
```

### DB is not healthy
```bash
# View PostgreSQL logs
docker logs iam_db

# Check healthcheck
docker inspect iam_db --format='{{.State.Health.Status}}'
```

### Port already in use
```bash
# See which process uses port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Change port in .env
PORT=8001
```
