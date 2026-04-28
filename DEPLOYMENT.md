# Guía de migraciones y deploy en producción

## Regla fundamental

**En producción solo se ejecuta `flask db upgrade`.**  
`flask db init` y `flask db migrate` son comandos de desarrollo. Nunca deben correr en producción ni en el entrypoint del contenedor.

---

## Flujo de desarrollo (local)

```sh
# 1. Modificar un modelo en app/models/
# 2. Generar la migración
flask db migrate -m "descripcion_del_cambio"

# 3. Revisar el archivo generado en migrations/versions/
# 4. Aplicar localmente para probar
flask db upgrade

# 5. Commitear la migración junto con los cambios al modelo
git add migrations/versions/<nuevo_archivo>.py
git commit -m "feat: <descripcion>"
```

---

## Qué se commitea

```
migrations/
├── alembic.ini
├── env.py
├── script.py.mako
└── versions/
    ├── c522f4503748_initial_migration.py
    ├── 0bf5825806bc_add_hr_models.py
    ├── ...
    └── f8b3c4d5e6f7_replace_base64_with_key_in_contratos.py  ← HEAD actual
```

`migrations/` **siempre debe estar en Git**. No se excluye en `.dockerignore`.

---

## Error: Can't locate revision identified by 'a21e252ee6ce'

### Diagnóstico

Este error significa que la tabla `alembic_version` en la base de datos contiene el ID `a21e252ee6ce`, pero ese archivo de migración no existe en `migrations/versions/`.

Ejecutar localmente contra la BD de producción:

```sh
flask db current    # muestra la revisión actual en la BD
flask db heads      # muestra el HEAD del árbol de migraciones
flask db history    # muestra el árbol completo
```

### Causas posibles

- La migración `a21e252ee6ce` existió en algún momento y fue eliminada del repositorio.
- La BD se creó con un árbol de migraciones diferente al actual.
- Se corrió `flask db init` + `flask db migrate` en producción, generando un historial nuevo que no coincide.

### Solución A — La BD está vacía o puede recrearse

```sh
# Desde Coolify, en el contenedor del backend:
flask db stamp head
```

Esto escribe el HEAD actual (`f8b3c4d5e6f7`) en `alembic_version` **sin correr ninguna migración**.  
Usar solo si la BD está vacía o si ya tiene el esquema correcto y solo falta sincronizar el historial.

### Solución B — La BD tiene datos y el esquema coincide con el código actual

```sql
-- Ejecutar directamente en MariaDB:
UPDATE alembic_version SET version_num = 'f8b3c4d5e6f7';
```

Luego verificar con `flask db current` que muestra `f8b3c4d5e6f7 (head)`.

### Solución C — Recuperar la migración perdida desde Git

```sh
git log --all --oneline -- "migrations/versions/*a21e252ee6ce*"
git show <commit_hash>:migrations/versions/<archivo>.py > migrations/versions/<archivo>.py
```

**Ninguna de estas soluciones debe automatizarse en el entrypoint.**  
Son operaciones manuales que requieren entender el estado de la base.

---

## Verificar estructura antes de cada deploy

```sh
# Árbol de migraciones correcto:
flask db history --verbose

# HEAD actual:
flask db heads

# Estado de la BD (requiere conexión a producción):
flask db current
```

El HEAD esperado actualmente es: `f8b3c4d5e6f7`  
Cadena: `c522f4503748 → 0bf5825806bc → a3f7d2c1e849 → c6f8901a2b3d → d1e2f3a4b5c6 → e7a1b2c3d4e5 → f8b3c4d5e6f7`

---

## Crear una nueva migración

```sh
# Siempre en desarrollo, nunca en producción
flask db migrate -m "add_column_X_to_table_Y"
flask db upgrade   # verificar localmente
git add migrations/
git commit
```
