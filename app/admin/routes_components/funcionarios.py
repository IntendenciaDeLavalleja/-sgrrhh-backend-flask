import json
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models.hr import (
    Cargo,
    Dependencia,
    EstadoCivilCat,
    EstadoEducacionCat,
    EstadoFuncionarioCat,
    Funcionario,
    GeneroCat,
    RegimenLaboral,
)
from app.utils.logging_helper import log_activity
from .. import admin_bp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _form_context():
    """Contexto compartido para formularios de funcionario."""
    dependencias = Dependencia.query.order_by(Dependencia.nombre).all()
    cargos = Cargo.query.order_by(Cargo.dependencia_id, Cargo.nombre).all()
    generos = GeneroCat.query.filter_by(activo=True).order_by(GeneroCat.orden, GeneroCat.nombre).all()
    estados_civiles = EstadoCivilCat.query.filter_by(activo=True).order_by(EstadoCivilCat.orden, EstadoCivilCat.nombre).all()
    estados_educacion = EstadoEducacionCat.query.filter_by(activo=True).order_by(EstadoEducacionCat.orden, EstadoEducacionCat.nombre).all()
    estados_funcionario = EstadoFuncionarioCat.query.filter_by(activo=True).order_by(EstadoFuncionarioCat.orden, EstadoFuncionarioCat.nombre).all()
    regimenes = RegimenLaboral.query.filter_by(activo=True).order_by(RegimenLaboral.orden, RegimenLaboral.nombre).all()

    # Mapa dep_id -> lista de cargos (para JS)
    cargos_por_dep = {}
    for c in cargos:
        key = str(c.dependencia_id)
        cargos_por_dep.setdefault(key, []).append({'id': c.id, 'nombre': c.nombre})

    return dict(
        dependencias=dependencias,
        cargos=cargos,
        generos=generos,
        estados_civiles=estados_civiles,
        estados_educacion=estados_educacion,
        estados_funcionario=estados_funcionario,
        regimenes=regimenes,
        cargos_por_dep_json=json.dumps(cargos_por_dep),
    )


def _parse_date(s):
    if s and s.strip():
        try:
            return datetime.strptime(s.strip(), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios')
@login_required
def funcionarios_list():
    q = request.args.get('q', '').strip()
    estado = request.args.get('estado', '')
    dep_id = request.args.get('dep_id', type=int)

    query = Funcionario.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Funcionario.nombres.ilike(like),
                Funcionario.apellidos.ilike(like),
                Funcionario.ci.ilike(like),
            )
        )
    if estado:
        query = query.filter(Funcionario.estado == estado)
    if dep_id:
        query = query.filter(Funcionario.dependencia_id == dep_id)

    funcionarios = query.order_by(Funcionario.apellidos, Funcionario.nombres).all()
    dependencias = Dependencia.query.order_by(Dependencia.nombre).all()
    estados = EstadoFuncionarioCat.query.filter_by(activo=True).order_by(EstadoFuncionarioCat.orden).all()

    return render_template(
        'admin/funcionarios_list.html',
        funcionarios=funcionarios,
        dependencias=dependencias,
        estados=estados,
        q=q,
        estado_sel=estado,
        dep_id_sel=dep_id,
    )


# ---------------------------------------------------------------------------
# Crear
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios/nuevo', methods=['GET', 'POST'])
@login_required
def funcionarios_nuevo():
    if request.method == 'POST':
        data = request.form
        ci = (data.get('ci') or '').strip()
        nombres = (data.get('nombres') or '').strip()
        apellidos = (data.get('apellidos') or '').strip()
        genero = data.get('genero') or ''
        dependencia_id = data.get('dependencia_id', type=int)
        cargo_id = data.get('cargo_id', type=int)
        fecha_ingreso_str = data.get('fecha_ingreso', '')
        regimen_laboral = data.get('regimen_laboral') or 'Full Time'
        estado = data.get('estado') or 'Presupuestado'

        errors = []
        if not ci:
            errors.append('La cédula es obligatoria.')
        elif Funcionario.query.filter_by(ci=ci).first():
            errors.append(f'Ya existe un funcionario con CI {ci}.')
        if not nombres:
            errors.append('Los nombres son obligatorios.')
        if not apellidos:
            errors.append('Los apellidos son obligatorios.')
        if not genero:
            errors.append('El género es obligatorio.')
        if not dependencia_id:
            errors.append('La dependencia es obligatoria.')
        if not cargo_id:
            errors.append('El cargo es obligatorio.')
        if not fecha_ingreso_str:
            errors.append('La fecha de ingreso es obligatoria.')

        fecha_ingreso = _parse_date(fecha_ingreso_str)
        if fecha_ingreso_str and fecha_ingreso is None:
            errors.append('Formato de fecha inválido (use AAAA-MM-DD).')

        if errors:
            for e in errors:
                flash(e, 'error')
            ctx = _form_context()
            return render_template('admin/funcionarios_form.html', modo='nuevo', form_data=data, **ctx)

        funcionario = Funcionario(
            ci=ci,
            nombres=nombres,
            apellidos=apellidos,
            genero=genero,
            fecha_nacimiento=_parse_date(data.get('fecha_nacimiento')),
            pais_nacimiento=data.get('pais_nacimiento') or None,
            departamento_nacimiento=data.get('departamento_nacimiento') or None,
            estado_civil=data.get('estado_civil') or None,
            dependencia_id=dependencia_id,
            cargo_id=cargo_id,
            fecha_ingreso=fecha_ingreso,
            regimen_laboral=regimen_laboral,
            estado=estado,
            motivo_baja=data.get('motivo_baja') or None,
            inasistencias=int(data.get('inasistencias') or 0),
            telefono=data.get('telefono') or None,
            email=data.get('email') or None,
            otro_contacto=data.get('otro_contacto') or None,
            calle=data.get('calle') or None,
            entre_calles=data.get('entre_calles') or None,
            zona=data.get('zona') or None,
            observaciones=data.get('observaciones') or None,
            educacion_primaria=data.get('educacion_primaria') or None,
            educacion_secundaria=data.get('educacion_secundaria') or None,
            educacion_bachillerato=data.get('educacion_bachillerato') or None,
            educacion_terciaria=data.get('educacion_terciaria') or None,
            otras_capacitaciones=data.get('otras_capacitaciones') or None,
        )
        db.session.add(funcionario)
        db.session.commit()
        log_activity('FUNC_CREATE', f'Funcionario creado: {nombres} {apellidos} (CI {ci})')
        flash(f'Funcionario {nombres} {apellidos} creado correctamente.', 'success')
        return redirect(url_for('admin.funcionarios_list'))

    ctx = _form_context()
    return render_template('admin/funcionarios_form.html', modo='nuevo', form_data={}, **ctx)


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios/<int:func_id>/editar', methods=['GET', 'POST'])
@login_required
def funcionarios_editar(func_id):
    funcionario = Funcionario.query.get_or_404(func_id)

    if request.method == 'POST':
        data = request.form
        ci = (data.get('ci') or '').strip()
        nombres = (data.get('nombres') or '').strip()
        apellidos = (data.get('apellidos') or '').strip()
        genero = data.get('genero') or ''
        dependencia_id = data.get('dependencia_id', type=int)
        cargo_id = data.get('cargo_id', type=int)
        fecha_ingreso_str = data.get('fecha_ingreso', '')
        regimen_laboral = data.get('regimen_laboral') or 'Full Time'
        estado = data.get('estado') or funcionario.estado

        errors = []
        if not ci:
            errors.append('La cédula es obligatoria.')
        elif Funcionario.query.filter(Funcionario.ci == ci, Funcionario.id != func_id).first():
            errors.append(f'Ya existe otro funcionario con CI {ci}.')
        if not nombres:
            errors.append('Los nombres son obligatorios.')
        if not apellidos:
            errors.append('Los apellidos son obligatorios.')
        if not genero:
            errors.append('El género es obligatorio.')
        if not dependencia_id:
            errors.append('La dependencia es obligatoria.')
        if not cargo_id:
            errors.append('El cargo es obligatorio.')
        if not fecha_ingreso_str:
            errors.append('La fecha de ingreso es obligatoria.')

        fecha_ingreso = _parse_date(fecha_ingreso_str)
        if fecha_ingreso_str and fecha_ingreso is None:
            errors.append('Formato de fecha inválido (use AAAA-MM-DD).')

        if errors:
            for e in errors:
                flash(e, 'error')
            ctx = _form_context()
            return render_template(
                'admin/funcionarios_form.html',
                modo='editar',
                funcionario=funcionario,
                form_data=data,
                **ctx,
            )

        funcionario.ci = ci
        funcionario.nombres = nombres
        funcionario.apellidos = apellidos
        funcionario.genero = genero
        funcionario.fecha_nacimiento = _parse_date(data.get('fecha_nacimiento'))
        funcionario.pais_nacimiento = data.get('pais_nacimiento') or None
        funcionario.departamento_nacimiento = data.get('departamento_nacimiento') or None
        funcionario.estado_civil = data.get('estado_civil') or None
        funcionario.dependencia_id = dependencia_id
        funcionario.cargo_id = cargo_id
        funcionario.fecha_ingreso = fecha_ingreso
        funcionario.regimen_laboral = regimen_laboral
        funcionario.estado = estado
        funcionario.motivo_baja = data.get('motivo_baja') or None
        funcionario.inasistencias = int(data.get('inasistencias') or 0)
        funcionario.telefono = data.get('telefono') or None
        funcionario.email = data.get('email') or None
        funcionario.otro_contacto = data.get('otro_contacto') or None
        funcionario.calle = data.get('calle') or None
        funcionario.entre_calles = data.get('entre_calles') or None
        funcionario.zona = data.get('zona') or None
        funcionario.observaciones = data.get('observaciones') or None
        funcionario.educacion_primaria = data.get('educacion_primaria') or None
        funcionario.educacion_secundaria = data.get('educacion_secundaria') or None
        funcionario.educacion_bachillerato = data.get('educacion_bachillerato') or None
        funcionario.educacion_terciaria = data.get('educacion_terciaria') or None
        funcionario.otras_capacitaciones = data.get('otras_capacitaciones') or None

        db.session.commit()
        log_activity('FUNC_UPDATE', f'Funcionario editado: {nombres} {apellidos} (CI {ci})')
        flash(f'Funcionario {nombres} {apellidos} actualizado correctamente.', 'success')
        return redirect(url_for('admin.funcionarios_list'))

    ctx = _form_context()
    return render_template(
        'admin/funcionarios_form.html',
        modo='editar',
        funcionario=funcionario,
        form_data={},
        **ctx,
    )


# ---------------------------------------------------------------------------
# Eliminar
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios/<int:func_id>/eliminar', methods=['POST'])
@login_required
def funcionarios_eliminar(func_id):
    funcionario = Funcionario.query.get_or_404(func_id)
    nombre = f'{funcionario.nombres} {funcionario.apellidos}'
    ci = funcionario.ci
    db.session.delete(funcionario)
    db.session.commit()
    log_activity('FUNC_DELETE', f'Funcionario eliminado: {nombre} (CI {ci})')
    flash(f'Funcionario {nombre} eliminado correctamente.', 'success')
    return redirect(url_for('admin.funcionarios_list'))
