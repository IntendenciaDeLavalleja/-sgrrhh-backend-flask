from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.hr import (
    Cargo,
    Dependencia,
    EstadoCivilCat,
    EstadoEducacionCat,
    EstadoFuncionarioCat,
    EstadoZafralCat,
    GeneroCat,
    RegimenLaboral,
    Tarea,
    TipoZafralCat,
)
from app.utils.logging_helper import log_activity
from .. import admin_bp


# ---------------------------------------------------------------------------
# Áreas (Dependencias) — entidad independiente compartida por ambos tipos
# ---------------------------------------------------------------------------

@admin_bp.route('/hr/areas', methods=['GET', 'POST'])
@login_required
def hr_areas():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        if not nombre:
            flash('El nombre es obligatorio', 'error')
        elif Dependencia.query.filter_by(nombre=nombre).first():
            flash(f'Ya existe un área llamada "{nombre}"', 'error')
        else:
            db.session.add(Dependencia(nombre=nombre))
            db.session.commit()
            log_activity('HR_AREA_CREATE', f'Área creada: {nombre}')
            flash(f'Área "{nombre}" creada correctamente', 'success')
        return redirect(url_for('admin.hr_areas'))

    areas = Dependencia.query.order_by(Dependencia.nombre).all()
    return render_template('admin/hr_areas.html', areas=areas)


@admin_bp.route('/hr/areas/<int:area_id>/update', methods=['POST'])
@login_required
def hr_update_area(area_id):
    area = Dependencia.query.get_or_404(area_id)
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio', 'error')
    else:
        area.nombre = nombre
        db.session.commit()
        log_activity('HR_AREA_UPDATE', f'Área actualizada: {nombre}')
        flash('Área actualizada', 'success')
    return redirect(url_for('admin.hr_areas'))


@admin_bp.route('/hr/areas/<int:area_id>/delete', methods=['POST'])
@login_required
def hr_delete_area(area_id):
    area = Dependencia.query.get_or_404(area_id)
    total = area.funcionarios.count() + area.funcionarios_zafrales.count()
    if total > 0:
        flash('No se puede eliminar: tiene funcionarios asociados', 'error')
    else:
        nombre = area.nombre
        db.session.delete(area)
        db.session.commit()
        log_activity('HR_AREA_DELETE', f'Área eliminada: {nombre}')
        flash(f'Área "{nombre}" eliminada', 'success')
    return redirect(url_for('admin.hr_areas'))


# ---------------------------------------------------------------------------
# Cargos — exclusivos de Funcionarios regulares
# ---------------------------------------------------------------------------

@admin_bp.route('/hr/cargos', methods=['GET', 'POST'])
@login_required
def hr_cargos():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        area_id = request.form.get('area_id', type=int)
        if not nombre or not area_id:
            flash('Nombre y área son obligatorios', 'error')
        else:
            db.session.add(Cargo(nombre=nombre, dependencia_id=area_id))
            db.session.commit()
            log_activity('HR_CARGO_CREATE', f'Cargo creado: {nombre}')
            flash(f'Cargo "{nombre}" creado', 'success')
        return redirect(url_for('admin.hr_cargos'))

    cargos = Cargo.query.order_by(Cargo.nombre).all()
    areas = Dependencia.query.order_by(Dependencia.nombre).all()
    return render_template('admin/hr_cargos.html', cargos=cargos, areas=areas)


@admin_bp.route('/hr/cargos/<int:cargo_id>/update', methods=['POST'])
@login_required
def hr_update_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio', 'error')
    else:
        cargo.nombre = nombre
        db.session.commit()
        log_activity('HR_CARGO_UPDATE', f'Cargo actualizado: {nombre}')
        flash('Cargo actualizado', 'success')
    return redirect(url_for('admin.hr_cargos'))


@admin_bp.route('/hr/cargos/<int:cargo_id>/delete', methods=['POST'])
@login_required
def hr_delete_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    if cargo.funcionarios.count() > 0:
        flash('No se puede eliminar: tiene funcionarios asociados', 'error')
    else:
        nombre = cargo.nombre
        db.session.delete(cargo)
        db.session.commit()
        log_activity('HR_CARGO_DELETE', f'Cargo eliminado: {nombre}')
        flash(f'Cargo "{nombre}" eliminado', 'success')
    return redirect(url_for('admin.hr_cargos'))


# ---------------------------------------------------------------------------
# Tareas — exclusivas de Funcionarios Zafrales
# ---------------------------------------------------------------------------

@admin_bp.route('/hr/tareas', methods=['GET', 'POST'])
@login_required
def hr_tareas():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        area_id = request.form.get('area_id', type=int)
        if not nombre or not area_id:
            flash('Nombre y área son obligatorios', 'error')
        else:
            db.session.add(Tarea(nombre=nombre, dependencia_id=area_id))
            db.session.commit()
            log_activity('HR_TAREA_CREATE', f'Tarea creada: {nombre}')
            flash(f'Tarea "{nombre}" creada', 'success')
        return redirect(url_for('admin.hr_tareas'))

    tareas = Tarea.query.order_by(Tarea.nombre).all()
    areas = Dependencia.query.order_by(Dependencia.nombre).all()
    return render_template('admin/hr_tareas.html', tareas=tareas, areas=areas)


@admin_bp.route('/hr/tareas/<int:tarea_id>/update', methods=['POST'])
@login_required
def hr_update_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio', 'error')
    else:
        tarea.nombre = nombre
        db.session.commit()
        log_activity('HR_TAREA_UPDATE', f'Tarea actualizada: {nombre}')
        flash('Tarea actualizada', 'success')
    return redirect(url_for('admin.hr_tareas'))


@admin_bp.route('/hr/tareas/<int:tarea_id>/delete', methods=['POST'])
@login_required
def hr_delete_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    if tarea.funcionarios_zafrales.count() > 0:
        flash('No se puede eliminar: tiene zafrales asociados', 'error')
    else:
        nombre = tarea.nombre
        db.session.delete(tarea)
        db.session.commit()
        log_activity('HR_TAREA_DELETE', f'Tarea eliminada: {nombre}')
        flash(f'Tarea "{nombre}" eliminada', 'success')
    return redirect(url_for('admin.hr_tareas'))


# ---------------------------------------------------------------------------
# Catálogos de opciones (regímenes, tipos, géneros, estados, etc.)
# ---------------------------------------------------------------------------

_CATALOGS: dict[str, tuple[str, type]] = {
    'regimenes': ('Regímenes Laborales', RegimenLaboral),
    'tipos-zafral': ('Tipos de Zafral', TipoZafralCat),
    'generos': ('Géneros', GeneroCat),
    'estados-civiles': ('Estados Civiles', EstadoCivilCat),
    'estados-educacion': ('Estados de Educación', EstadoEducacionCat),
    'estados-funcionario': ('Estados de Funcionario', EstadoFuncionarioCat),
    'estados-zafral': ('Estados Funcionario Zafral', EstadoZafralCat),
}


@admin_bp.route('/hr/opciones', methods=['GET'])
@login_required
def hr_opciones():
    data: dict = {}
    for key, (label, model) in _CATALOGS.items():
        data[key] = {
            'label': label,
            'registros': model.query.order_by(model.orden, model.nombre).all(),
        }
    return render_template('admin/hr_opciones.html', catalogs=data, catalog_keys=list(_CATALOGS.keys()))


@admin_bp.route('/hr/opciones/<cat>', methods=['POST'])
@login_required
def hr_create_opcion(cat):
    if cat not in _CATALOGS:
        flash('Catálogo no válido', 'error')
        return redirect(url_for('admin.hr_opciones'))

    label, model = _CATALOGS[cat]
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio', 'error')
    elif model.query.filter_by(nombre=nombre).first():
        flash(f'"{nombre}" ya existe en {label}', 'error')
    else:
        db.session.add(model(nombre=nombre))
        db.session.commit()
        log_activity('HR_OPCION_CREATE', f'{label}: creado "{nombre}"')
        flash(f'"{nombre}" agregado a {label}', 'success')
    return redirect(url_for('admin.hr_opciones') + f'#tab-{cat}')


@admin_bp.route('/hr/opciones/<cat>/<int:item_id>/update', methods=['POST'])
@login_required
def hr_update_opcion(cat, item_id):
    if cat not in _CATALOGS:
        flash('Catálogo no válido', 'error')
        return redirect(url_for('admin.hr_opciones'))

    label, model = _CATALOGS[cat]
    item = model.query.get_or_404(item_id)
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio', 'error')
    else:
        item.nombre = nombre
        db.session.commit()
        log_activity('HR_OPCION_UPDATE', f'{label}: actualizado a "{nombre}"')
        flash(f'"{nombre}" actualizado', 'success')
    return redirect(url_for('admin.hr_opciones') + f'#tab-{cat}')


@admin_bp.route('/hr/opciones/<cat>/<int:item_id>/toggle', methods=['POST'])
@login_required
def hr_toggle_opcion(cat, item_id):
    if cat not in _CATALOGS:
        flash('Catálogo no válido', 'error')
        return redirect(url_for('admin.hr_opciones'))

    label, model = _CATALOGS[cat]
    item = model.query.get_or_404(item_id)
    item.activo = not item.activo
    db.session.commit()
    estado = 'activado' if item.activo else 'desactivado'
    log_activity('HR_OPCION_TOGGLE', f'{label}: "{item.nombre}" {estado}')
    flash(f'"{item.nombre}" {estado}', 'success')
    return redirect(url_for('admin.hr_opciones') + f'#tab-{cat}')


@admin_bp.route('/hr/opciones/<cat>/<int:item_id>/delete', methods=['POST'])
@login_required
def hr_delete_opcion(cat, item_id):
    if cat not in _CATALOGS:
        flash('Catálogo no válido', 'error')
        return redirect(url_for('admin.hr_opciones'))

    label, model = _CATALOGS[cat]
    item = model.query.get_or_404(item_id)
    nombre = item.nombre
    db.session.delete(item)
    db.session.commit()
    log_activity('HR_OPCION_DELETE', f'{label}: eliminado "{nombre}"')
    flash(f'"{nombre}" eliminado de {label}', 'success')
    return redirect(url_for('admin.hr_opciones') + f'#tab-{cat}')
