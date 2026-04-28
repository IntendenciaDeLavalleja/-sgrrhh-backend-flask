import uuid
from flask import Flask, g, request
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, login_manager, mail, ma, limiter, csrf, jwt
from .services.cache_service import cache_service
from .metrics import init_metrics
from .redis_utils import init_redis
from .error_handlers import register_error_handlers


def _init_limiter_safe(app):
    """
    Inicializa Flask-Limiter de forma segura.

    Intenta usar Redis como storage si está disponible.
    Si falla por cualquier motivo, fuerza el fallback a memory://
    y vuelve a inicializar. Nunca lanza excepciones.
    """
    redis_available = app.config.get('REDIS_AVAILABLE', False)
    redis_url = app.config.get('REDIS_URL', '')

    if redis_available and redis_url:
        app.config['RATELIMIT_STORAGE_URI'] = redis_url
    else:
        app.config['RATELIMIT_STORAGE_URI'] = 'memory://'

    try:
        limiter.init_app(app)
        storage_used = app.config['RATELIMIT_STORAGE_URI']
        app.logger.info(
            f"Flask-Limiter inicializado con storage: {storage_used}"
        )
    except Exception as exc:
        app.logger.warning(
            f"Flask-Limiter falló con storage actual: {exc}. "
            "Reintentando con memory://"
        )
        # Forzar fallback y reintentar una vez.
        app.config['RATELIMIT_STORAGE_URI'] = 'memory://'
        try:
            limiter.init_app(app)
            app.logger.info(
                "Flask-Limiter inicializado con fallback memory://"
            )
        except Exception as exc2:
            # Último recurso: loguear y continuar sin Limiter funcional.
            app.logger.error(
                f"Flask-Limiter no pudo inicializarse: {exc2}. "
                "Rate limiting deshabilitado para esta sesión."
            )


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../public', static_url_path='/public')
    app.config.from_object(config_class)

    # Probar Redis y almacenar disponibilidad en app.config['REDIS_AVAILABLE'].
    # init_redis() nunca lanza excepciones: es seguro siempre.
    init_redis(app)

    # Habilitar CORS
    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])}
        },
        supports_credentials=True
    )

    # Inicializar extensiones base
    db.init_app(app)
    migrate.init_app(app, db)

    # Asegurar encoding UTF-8 en cada conexión si es MariaDB/MySQL
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'mariadb' in db_uri or 'mysql' in db_uri:
        from sqlalchemy import event
        with app.app_context():
            @event.listens_for(db.engine, 'connect')
            def set_unicode(dbapi_conn, conn_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()

    login_manager.init_app(app)
    mail.init_app(app)
    ma.init_app(app)
    csrf.init_app(app)
    jwt.init_app(app)

    # Inicializar Flask-Limiter con fallback automático a memory://.
    _init_limiter_safe(app)

    # Inicializar servicios
    cache_service.init_app(app)

    from .services.minio_service import minio_service
    minio_service.init_app(app)

    # Inicializar monitoreo
    init_metrics(app)

    @app.before_request
    def attach_request_id():
        # Correlation id para rastrear errores entre Gunicorn y Flask.
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    @app.after_request
    def add_request_id_header(response):
        request_id = getattr(g, 'request_id', None)
        if request_id:
            response.headers['X-Request-ID'] = request_id
        return response

    @app.teardown_request
    def teardown_request(_exc):
        # Garantiza limpieza de sesión por request para evitar sesiones sucias.
        db.session.remove()

    # Registrar blueprints
    from .health import health_bp
    csrf.exempt(health_bp)
    app.register_blueprint(health_bp)

    from .api import api_bp
    csrf.exempt(api_bp)  # Eximir API de protección CSRF (usa tokens Bearer)
    app.register_blueprint(api_bp, url_prefix='/api')

    from .admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Registrar handlers globales de errores al final para cubrir toda la app.
    register_error_handlers(app)

    # Registrar comandos CLI
    from .commands import create_admin, init_db
    from .hr_seed import seed_hr_data, seed_zafrales_data, seed_catalog_data
    app.cli.add_command(create_admin)
    app.cli.add_command(init_db)
    app.cli.add_command(seed_hr_data)
    app.cli.add_command(seed_zafrales_data)
    app.cli.add_command(seed_catalog_data)

    # Cargar modelos para migraciones
    import importlib
    importlib.import_module('app.models')

    return app


@login_manager.user_loader
def load_user(user_id):
    from .models import AdminUser

    return AdminUser.query.get(int(user_id))
