# 🔐 IAM Service

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-170+-brightgreen.svg)](tests/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-purple.svg)](tools/)

> A production-ready Identity and Access Management (IAM) microservice built with FastAPI, implementing enterprise-grade security patterns and modern software architecture principles.

**[Español](docs/spanish/README.es.md)** | English

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [MCP Integration](#-mcp-integration)
- [Contributing](#-contributing)

---

## 🌟 Overview

This IAM Service is a lightweight, personal version derived from a real professional project. It provides a complete solution for identity and access management, including user authentication, authorization, role-based access control (RBAC), and client application management.

### What is this for?

- **Microservices Authentication**: Secure authentication and authorization for distributed systems
- **Multi-tenant Applications**: Manage users, roles, and permissions across different clients
- **API Gateway Security**: Centralized identity provider for API ecosystems
- **Learning & Experimentation**: Well-documented, clean architecture for studying modern IAM patterns

---

## ✨ Key Features

### 🔒 Security & Authentication

- **JWT-based Authentication** with access and refresh tokens
- **Secure Password Hashing** using Argon2 and bcrypt
- **Refresh Token Rotation** with blacklist support and multiplatform
- **Machine-to-Machine (M2M) Authentication** for client applications
- **Password Policies** with customizable business rules
- **Cookie-based Refresh Tokens** with HTTP-only and secure flags

### 👥 User Management

- **Self-service User Registration** with email validation
- **Admin User Creation** with temporary passwords
- **User Profile Management** (update, activate/deactivate, delete)
- **Email Change Flow** with password confirmation
- **Password Change** with old password validation
- **Force Password Change** on first login for admin-created users

### 🎭 Role-Based Access Control (RBAC)

- **Granular Permissions System** with 16+ predefined permissions
- **Dynamic Role Management** (create, update, delete roles)
- **Role-Permission Assignment** with flexible composition
- **User-Role Assignment** for multi-role support
- **Superuser Support** for administrative access
- **Permission Guards** with decorator-based protection

### 🔌 Client Applications

- **Client Credentials Flow** (OAuth 2.0)
- **Client-Permission Assignment** for scoped access
- **Secret Management** with secure generation and hashing
- **Client Activation/Deactivation** controls

### 🧪 Quality Assurance

- **170+ Comprehensive Tests**:
  - Unit tests for services and repositories
  - Integration tests for API endpoints
  - End-to-end tests for complete workflows
  - Security tests for vulnerability detection
  - Performance tests for load validation
- **90%+ Code Coverage**
- **Type Checking** with Pydantic v2
- **Linting & Formatting** with Ruff and Black

### 🚀 CI/CD Pipeline

- **Automated GitHub Actions Workflow** triggered on every push and PR:
  - **Code Quality Check**: Ruff linter + Black formatter verification
  - **Security Scan**: Safety (dependency vulnerabilities) + Bandit (code security issues)
  - **Test Suite**: Full test execution with coverage reporting (Codecov integration)
  - **Production Build**: Docker image build verification
  - **Status Gate**: Merge blocking if any check fails
- **Multi-Stage Pipeline**: Parallel execution for faster feedback
- **Artifact Retention**: Security reports stored for 7 days
- **Docker-based Testing**: Isolated test environment with PostgreSQL

### 📊 Structured Logging System

- **JSON Formatted Logs** for easy parsing and analysis
- **Request Tracing**: Unique `request_id` for tracking requests across the system
- **User Context**: Automatic `user_id`/`client_id` injection in all log entries
- **Privacy Masking**: Configurable privacy levels (none, standard, strict)
  - Email masking: `user@domain.com` → `u***@d***.com`
  - UUID masking: Full UUIDs shortened for log safety
  - Sensitive data protection in logs
- **Performance Metrics**: Automatic duration tracking for all HTTP requests
- **Contextual Information**:
  - Timestamp (ISO 8601 UTC)
  - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Module and function name
  - HTTP method, path, route, status code
- **X-Request-Id Header**: Response header for client-side correlation
- **Third-Party Logger Management**: Controlled logging for uvicorn, SQLAlchemy, asyncio

### 🤖 AI & Developer Tools

- **MCP (Model Context Protocol) Compatible** for LLM integration
- **Multiple Tool Export Formats**: JSON, TOML, YAML, LangChain
- **OpenAPI/Swagger Documentation** with interactive UI
- **ReDoc Documentation** for detailed API reference

---

## 🏗️ Architecture

This project follows **Clean Architecture** and **Layered Architecture** principles with modern software design patterns:

### Design Patterns & Principles

#### 🎯 Core Patterns

- **Repository Pattern**: Abstraction layer for data access logic
- **Service Layer Pattern**: Business logic encapsulation and orchestration
- **Unit of Work Pattern**: Transaction management across multiple repositories
- **Dependency Injection**: Loose coupling and testability with FastAPI's dependency system
- **Strategy Pattern**: Flexible password hashing algorithm selection
- **Factory Pattern**: Dynamic object creation (tokens, sessions)

#### 🧱 Architectural Layers

```
┌─────────────────────────────────────────┐
│          API Layer (Routes)             │
│  ┌─────────────────────────────────┐    │
│  │    FastAPI Endpoints & DTOs     │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Middleware & Dependencies         │
│  ┌─────────────────────────────────┐    │
│  │  Auth, Logging, Context, CORS   │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Service Layer (Business)        │
│  ┌─────────────────────────────────┐    │
│  │   Business Logic & Validation   │    │
│  │   UserService, AuthService...   │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Repository Layer (Data Access)     │
│  ┌─────────────────────────────────┐    │
│  │  CRUD Operations & Queries      │    │
│  │  UserRepo, RoleRepo...          │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Database Layer (ORM)            │
│  ┌─────────────────────────────────┐    │
│  │  SQLAlchemy Models & Schemas    │    │
│  │  PostgreSQL Database            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

#### 📂 Project Structure

```
IAM_Service/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── services/         # Business logic layer
│   ├── repositories/     # Data access layer
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic DTOs
│   ├── core/             # Core configurations and security
│   ├── db/               # Database session and UoW
│   ├── middleware/       # Request/response middleware
│   └── dependencies/     # FastAPI dependencies
├── tests/                # Comprehensive test suite
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
├── tools/                # MCP tools export
└── docs/                 # Documentation
```

---

## 🛠️ Tech Stack

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance web framework
- **[Python 3.12+](https://www.python.org/)** - Latest Python features and performance
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** - Async ORM
- **[Pydantic v2](https://docs.pydantic.dev/)** - Data validation
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migration tool

### Database

- **[PostgreSQL 15+](https://www.postgresql.org/)** - Relational database

### Security

- **[python-jose](https://github.com/mpdavis/python-jose)** - JWT implementation
- **[passlib](https://passlib.readthedocs.io/)** - Password hashing (Argon2, bcrypt)
- **[python-multipart](https://github.com/andrew-d/python-multipart)** - Form data parsing

### Testing

- **[pytest](https://pytest.org/)** - Testing framework
- **[pytest-asyncio](https://pytest-asyncio.readthedocs.io/)** - Async test support
- **[pytest-cov](https://pytest-cov.readthedocs.io/)** - Coverage reporting
- **[httpx](https://www.python-httpx.org/)** - Async HTTP client for testing

### DevOps

- **[Docker](https://www.docker.com/)** - Containerization
- **[Docker Compose](https://docs.docker.com/compose/)** - Multi-container orchestration
- **[Gunicorn](https://gunicorn.org/)** - WSGI HTTP Server
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server

### Code Quality

- **[Ruff](https://github.com/astral-sh/ruff)** - Fast Python linter
- **[Black](https://black.readthedocs.io/)** - Code formatter

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.12+** (for local development)
- **PostgreSQL 15+** (if running without Docker)

### Quick Start with Docker

1. **Clone the repository**

```bash
git clone https://github.com/AI-Iex/IAM_Service.git
cd IAM_Service
```

2. **Create environment file**

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Service Configuration
SERVICE_NAME=IAM Service
SERVICE_VERSION=1
SERVICE_DESCRIPTION=Identity and Access Management Service
SERVICE_LICENSE=MIT

# Database
DATABASE_URL=postgresql+asyncpg://iam_user:password@db:5432/iam_db
TEST_DATABASE_URL=postgresql+asyncpg://iam_user:password@db_test:5432/iam_db_test

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_SECRET=your-super-secret-refresh-key-change-this
REFRESH_TOKEN_EXPIRE_DAYS=7

# Superuser (will be created on first startup if enabled)
CREATE_SUPERUSER_ON_STARTUP=true
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=ChangeThisPassword123!
SUPERUSER_NAME=Admin User

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Paths
SERVICE_PERMISSIONS_PATH=app/config/permissions_map.json
BUSINESS_RULES_PATH=app/config/business_rules.json
LOGGING_CONFIG_PATH=app/config/log_schema.json
```

3. **Start the services**

```bash
# Start with database (development)
docker-compose --profile with-db up -d

# Or start only the API (if you have external DB)
docker-compose up -d
```

4. **Run migrations and seed data**

```bash
docker-compose exec app python scripts/migrate_and_seed.py
```

5. **Access the application**

- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### Local Development Setup

1. **Create virtual environment**

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Set up database**

```bash
# Start PostgreSQL with Docker
docker-compose --profile with-db up -d db

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/migrate_and_seed.py
```

4. **Run the application**

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📚 API Documentation

### Available Endpoints

#### 🔐 Authentication (`/api/v1/auth`)

- `POST /auth` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and invalidate token
- `POST /auth/logout_all_devices` - Logout and invalidate all refresh tokens
- `POST /auth/client` - Client credentials authentication

#### 👥 Users (`/api/v1/users`)

- `POST /users` - Create user (admin)
- `GET /users` - List users with filters
- `GET /users/me` - Get current user profile
- `GET /users/{user_id}` - Get user by ID
- `PATCH /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user
- `PUT /users/{user_id}/email` - Change user email
- `PUT /users/{user_id}/password` - Change user password
- `POST /users/{user_id}/roles/{role_id}` - Assign role to user
- `DELETE /users/{user_id}/roles/{role_id}` - Remove role from user

#### 🎭 Roles (`/api/v1/roles`)

- `POST /roles` - Create role
- `GET /roles` - List roles with filters
- `GET /roles/{role_id}` - Get role by ID
- `PATCH /roles/{role_id}` - Update role
- `DELETE /roles/{role_id}` - Delete role
- `POST `/roles/{role_id}/permissions/{permission_id}` - Add permission to role
- `DELETE `/roles/{role_id}/permissions/{permission_id}` - Remove permission from role

#### 🔑 Permissions (`/api/v1/permissions`)

- `POST /permissions` - Create permission
- `GET /permissions` - List permissions with filters
- `GET /permissions/{permission_id}` - Get permission by ID
- `PATCH /permissions/{permission_id}` - Update permission
- `DELETE /permissions/{permission_id}` - Delete permission

#### 🔌 Clients (`/api/v1/clients`)

- `POST /clients` - Create client application
- `GET /clients` - List clients with filters
- `GET /clients/me` - Get current client profile
- `GET /clients/{client_id}` - Get client by ID
- `PATCH /clients/{client_id}` - Update client
- `DELETE /clients/{client_id}` - Delete client
- `POST /clients/{client_id}/permissions` - Assign permissions to client
- `DELETE /clients/{client_id}/permissions` - Remove permissions from client

#### ❤️ Health (`/api/v1/health`)

- `GET /health` - Health check endpoint

### Interactive Documentation

Once the service is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Testing

### Run All Tests

```bash
# With coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/security/
pytest tests/performance/
```

### Test Structure

```
tests/
├── unit/                 # Unit tests for services, repositories
├── integration/          # Integration tests for API endpoints
├── e2e/                  # End-to-end workflow tests
├── security/             # Security vulnerability tests
├── performance/          # Load and performance tests
└── conftest.py           # Test fixtures and configuration
```

### Coverage Report

After running tests with coverage, open `htmlcov/index.html` in your browser to see detailed coverage reports.

---

## 🤖 MCP Integration

This service is compatible with **Model Context Protocol (MCP)**, enabling seamless integration with Large Language Models (LLMs) for AI-powered identity management.

### Generate MCP Tools

```bash
# Generate all formats
python scripts/tools_generator.py

# Generate specific format
python scripts/tools_generator.py --format toml
python scripts/tools_generator.py --format langchain
python scripts/tools_generator.py --format json
```

### Available Tool Formats

- **JSON** (`tools/iam_tools.json`) - Standard MCP format
- **TOML** (`tools/iam_tools.toml`) - TOML configuration
- **YAML** (`tools/iam_tools.yaml`) - YAML configuration
- **LangChain** (`tools/iam_tools_langchain.json`) - LangChain integration
- **MCP Native** (`tools/iam_tools_mcp.json`) - Native MCP format

### Use Cases with LLMs

- **Automated User Provisioning**: "Create a new user with editor role"
- **Access Management**: "Grant read permissions to the analytics role"
- **Audit Queries**: "List all users with admin privileges"
- **Security Reviews**: "Show all permissions assigned to this client"

---

## 🤝 Contributing

Contributions are welcome! This project is open for improvements, bug fixes, and feature additions.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow the existing code style (Ruff + Black)
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR
- Keep commits atomic and well-described

### Reporting Issues

Found a bug or have a suggestion? Please [open an issue](https://github.com/AI-Iex/IAM_Service/issues) with:

- Clear description of the problem/suggestion
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

---

## 📧 Contact

**Alejandro Sastre**

- Email: alexsastre099@gmail.com
- GitHub: [@AI-Iex](https://github.com/AI-Iex)

<div align="center">

**[⬆ Back to Top](#-iam-service)**

By [Alejandro Sastre](https://github.com/AI-Iex)

</div>
