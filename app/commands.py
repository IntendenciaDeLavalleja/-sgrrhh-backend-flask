import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import AdminUser


@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@click.argument('is_superuser', default='false')
@with_appcontext
def create_admin(username, email, password, is_superuser):
    """Crea un usuario administrador."""
    is_super = is_superuser.lower() == 'true'
    user = AdminUser(username=username, email=email, is_superuser=is_super)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    role = "Super Administrador" if is_super else "Administrador"
    print(f"{role} {username} creado exitosamente.")


@click.command('init-db')
@with_appcontext
def init_db():
    """Inicializa la base de datos."""
    db.create_all()
    print("Base de datos inicializada.")
