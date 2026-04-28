from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import AdminUser
from app.utils.logging_helper import log_activity
from .. import admin_bp


def _superuser_required():
    if not current_user.is_authenticated or not current_user.is_superuser:
        abort(403)


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------

@admin_bp.route('/usuarios')
@login_required
def usuarios_list():
    _superuser_required()
    usuarios = AdminUser.query.order_by(AdminUser.username.asc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


# ---------------------------------------------------------------------------
# Crear
# ---------------------------------------------------------------------------

@admin_bp.route('/usuarios/crear', methods=['POST'])
@login_required
def usuarios_crear():
    _superuser_required()

    username        = (request.form.get('username') or '').strip()
    email           = (request.form.get('email') or '').strip().lower()
    password        = request.form.get('password') or ''
    password_confirm = request.form.get('password_confirm') or ''
    is_super        = request.form.get('is_superuser') == '1'

    if not username or not email or not password:
        flash('Nombre de usuario, email y contraseña son obligatorios.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    if len(password) < 8:
        flash('La contraseña debe tener al menos 8 caracteres.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    if password != password_confirm:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    if AdminUser.query.filter_by(username=username).first():
        flash(f'Ya existe un usuario con el nombre "{username}".', 'error')
        return redirect(url_for('admin.usuarios_list'))

    if AdminUser.query.filter_by(email=email).first():
        flash(f'Ya existe un usuario con el email "{email}".', 'error')
        return redirect(url_for('admin.usuarios_list'))

    nuevo = AdminUser(username=username, email=email, is_superuser=is_super)
    nuevo.set_password(password)
    db.session.add(nuevo)
    db.session.commit()
    rol = 'Super Admin' if is_super else 'Admin'
    log_activity('ADMIN_USER_CREATE', f'{rol} creado: {username} ({email})')
    flash(f'{rol} "{username}" creado correctamente.', 'success')
    return redirect(url_for('admin.usuarios_list'))


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------

@admin_bp.route('/usuarios/<int:user_id>/editar', methods=['POST'])
@login_required
def usuarios_editar(user_id):
    _superuser_required()

    usuario  = AdminUser.query.get_or_404(user_id)
    username = (request.form.get('username') or '').strip()
    email    = (request.form.get('email') or '').strip().lower()
    is_super = request.form.get('is_superuser') == '1'
    current_pass  = request.form.get('current_password') or ''
    new_pass      = request.form.get('password') or ''
    confirm_pass  = request.form.get('password_confirm') or ''

    if not username or not email:
        flash('Nombre de usuario y email son obligatorios.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    # Verificar contraseña actual del super-admin que ejecuta la acción
    if not current_user.check_password(current_pass):
        flash('Contraseña actual incorrecta. No se realizaron cambios.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    # Unicidad: ignorar el propio registro
    dup_user = AdminUser.query.filter(AdminUser.username == username, AdminUser.id != user_id).first()
    if dup_user:
        flash(f'Ya existe otro usuario con el nombre "{username}".', 'error')
        return redirect(url_for('admin.usuarios_list'))

    dup_email = AdminUser.query.filter(AdminUser.email == email, AdminUser.id != user_id).first()
    if dup_email:
        flash(f'Ya existe otro usuario con el email "{email}".', 'error')
        return redirect(url_for('admin.usuarios_list'))

    # Impedir que un super-admin se quite sus propios privilegios
    if usuario.id == current_user.id and not is_super:
        flash('No puedes quitarte tus propios privilegios de Super Admin.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    usuario.username     = username
    usuario.email        = email
    usuario.is_superuser = is_super

    if new_pass:
        if len(new_pass) < 8:
            flash('La nueva contraseña debe tener al menos 8 caracteres.', 'error')
            return redirect(url_for('admin.usuarios_list'))
        if new_pass != confirm_pass:
            flash('Las contraseñas nuevas no coinciden.', 'error')
            return redirect(url_for('admin.usuarios_list'))
        usuario.set_password(new_pass)

    db.session.commit()
    log_activity('ADMIN_USER_UPDATE', f'Usuario actualizado: {username} ({email})')
    flash(f'Usuario "{username}" actualizado.', 'success')
    return redirect(url_for('admin.usuarios_list'))


# ---------------------------------------------------------------------------
# Activar / Desactivar
# ---------------------------------------------------------------------------

@admin_bp.route('/usuarios/<int:user_id>/toggle', methods=['POST'])
@login_required
def usuarios_toggle(user_id):
    _superuser_required()

    usuario = AdminUser.query.get_or_404(user_id)

    if usuario.id == current_user.id:
        flash('No puedes desactivarte a ti mismo.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    usuario.is_active = not usuario.is_active
    db.session.commit()
    estado = 'activado' if usuario.is_active else 'desactivado'
    log_activity('ADMIN_USER_TOGGLE', f'Usuario {estado}: {usuario.username}')
    flash(f'Usuario "{usuario.username}" {estado}.', 'success')
    return redirect(url_for('admin.usuarios_list'))


# ---------------------------------------------------------------------------
# Eliminar
# ---------------------------------------------------------------------------

@admin_bp.route('/usuarios/<int:user_id>/eliminar', methods=['POST'])
@login_required
def usuarios_eliminar(user_id):
    _superuser_required()

    usuario = AdminUser.query.get_or_404(user_id)

    if usuario.id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'error')
        return redirect(url_for('admin.usuarios_list'))

    nombre = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    log_activity('ADMIN_USER_DELETE', f'Usuario eliminado: {nombre}')
    flash(f'Usuario "{nombre}" eliminado.', 'success')
    return redirect(url_for('admin.usuarios_list'))
