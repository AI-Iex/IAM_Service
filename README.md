## Commands Utils

# AI Tools Script
```bash
# Generate all formats
python scripts/generate_tools.py

# Only TOML
python scripts/generate_tools.py --format toml

# Only LangChain format
python scripts/generate_tools.py --format langchain

# Change Output
python scripts/generate_tools.py --output ./tools
```

## 📂 Project Structure 

```
IAM_Service
├─ .dockerignore
├─ alembic
│  ├─ env.py
│  └─ versions
│     ├─ 0001_initial.py
│     └─ README.md
├─ alembic.ini
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
├─ docker-compose.override.yml
├─ docker-compose.prod.yml
├─ docker-compose.yml
├─ Dockerfile
├─ docs
│  ├─ english
│  │  └─ docker-commands.md
│  └─ spanish
│     └─ docker-commands.md
├─ pyproject.toml
├─ pytest.ini
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ create_superuser.py
│  ├─ migrate_and_seed.py
│  ├─ setup_test_db.py
│  └─ tools_generator.py
├─ tests
│  ├─ conftest.py
│  ├─ connection
│  │  └─ test_connection.py
│  ├─ e2e
│  │  └─ test_full_user_role_permission_flow.py
│  ├─ integration
│  │  └─ api
│  │     ├─ test_auth_routes.py
│  │     ├─ test_clients_routes.py
│  │     ├─ test_permissions_routes.py
│  │     ├─ test_roles_routes.py
│  │     └─ test_users_routes.py
│  ├─ performance
│  │  ├─ test_database_query_latency.py
│  │  └─ test_password_hashing_speed.py
│  ├─ security
│  │  ├─ test_hash_passwords.py
│  │  └─ test_jwt_generation_and_validation.py
│  ├─ unit
│  │  ├─ core
│  │  │  ├─ test_config.py
│  │  │  ├─ test_exceptions.py
│  │  │  ├─ test_logging_config.py
│  │  │  └─ test_permissions_loader.py
│  │  ├─ db
│  │  │  ├─ test_bootstrap.py
│  │  │  ├─ test_session.py
│  │  │  └─ test_unit_of_work.py
│  │  ├─ middleware
│  │  │  ├─ test_context.py
│  │  │  └─ test_exception_handler.py
│  │  ├─ repositories
│  │  │  ├─ test_auth_repository.py
│  │  │  ├─ test_client_repository.py
│  │  │  ├─ test_permission_repository.py
│  │  │  ├─ test_refresh_token_repository.py
│  │  │  ├─ test_role_repository.py
│  │  │  └─ test_user_repository.py
│  │  └─ services
│  │     ├─ test_auth_service.py
│  │     ├─ test_client_service.py
│  │     ├─ test_permission_service.py
│  │     ├─ test_role_service.py
│  │     └─ test_user_service.py
│  └─ __init__.py
└─ tools
   ├─ iam_tools.json
   ├─ iam_tools.toml
   ├─ iam_tools.yaml
   ├─ iam_tools_langchain.json
   └─ iam_tools_mcp.json
```