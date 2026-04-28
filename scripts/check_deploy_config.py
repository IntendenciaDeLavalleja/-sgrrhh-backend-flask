"""
Valida que la configuración de entorno sea correcta antes de un deploy.

Uso:
    python scripts/check_deploy_config.py

No modifica nada, no conecta a la base, no hace cambios destructivos.
Sale con código 0 si todo está bien, 1 si hay problemas.
"""
import os
import sys

errors = []
warnings = []


def check(condition: bool, error_msg: str) -> None:
    if not condition:
        errors.append(error_msg)


def warn(condition: bool, warn_msg: str) -> None:
    if not condition:
        warnings.append(warn_msg)


# ── DATABASE_URL ──────────────────────────────────────────────────────────────
db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI", "")
check(bool(db_url), "DATABASE_URL is not set.")
if db_url:
    check(
        "://" in db_url,
        f"DATABASE_URL does not look like a valid URI: {db_url[:30]}..."
    )

# ── APP_MODULE ────────────────────────────────────────────────────────────────
app_module = os.getenv("APP_MODULE", "app:create_app()")
check(
    ":" in app_module,
    f"APP_MODULE must be in 'module:object' format, got: '{app_module}'"
)

# ── RUN_MIGRATIONS ────────────────────────────────────────────────────────────
run_migrations = os.getenv("RUN_MIGRATIONS", "false").lower()
check(
    run_migrations in ("true", "false"),
    f"RUN_MIGRATIONS must be 'true' or 'false', got: '{run_migrations}'"
)

if run_migrations == "true":
    migrations_env = os.path.join(os.path.dirname(__file__), "..", "migrations", "env.py")
    check(
        os.path.isfile(migrations_env),
        "RUN_MIGRATIONS=true but migrations/env.py does not exist. "
        "Commit the migrations/ folder to Git before enabling migrations."
    )

warn(
    run_migrations == "false",
    "RUN_MIGRATIONS=true — make sure migrations/ is committed and the DB is ready."
)

# ── SECRET_KEY ────────────────────────────────────────────────────────────────
secret_key = os.getenv("SECRET_KEY", "")
warn(
    secret_key not in ("", "you-will-never-guess", "CHANGE_ME_USE_A_LONG_RANDOM_STRING"),
    "SECRET_KEY is using a default/placeholder value. Set a strong random key."
)

# ── Report ────────────────────────────────────────────────────────────────────
if warnings:
    print("WARNINGS:")
    for w in warnings:
        print(f"  ⚠  {w}")
    print()

if errors:
    print("ERRORS:")
    for e in errors:
        print(f"  ✗  {e}")
    print()
    print("Deploy config check FAILED.")
    sys.exit(1)

print("Deploy config check PASSED.")
if warnings:
    print(f"({len(warnings)} warning(s) above — review before going live)")
