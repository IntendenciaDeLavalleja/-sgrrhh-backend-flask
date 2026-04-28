import json
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models.hr import (
    Dependencia,
    EstadoCivilCat,
    EstadoEducacionCat,
    EstadoZafralCat,
    FuncionarioZafral,
    GeneroCat,
    RegimenLaboral,
    Tarea,
    TipoZafralCat,
)
from app.utils.logging_helper import log_activity
from .. import admin_bp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _form_context_zafral():
    """Contexto compartido para formularios de funcionario zafral."""
    dependencias = Dependencia.query.order_by(Dependencia.nombre).all()
    tareas = Tarea.query.order_by(Tarea.dependencia_id, Tarea.nombre).all()
    generos = GeneroCat.query.filter_by(activo=True).order_by(GeneroCat.orden, GeneroCat.nombre).all()
    estados_civiles = EstadoCivilCat.query.filter_by(activo=True).order_by(EstadoCivilCat.orden, EstadoCivilCat.nombre).all()
    estados_educacion = EstadoEducacionCat.query.filter_by(activo=True).order_by(EstadoEducacionCat.orden, EstadoEducacionCat.nombre).all()
    estados_zafral = EstadoZafralCat.query.filter_by(activo=True).order_by(EstadoZafralCat.orden, EstadoZafralCat.nombre).all()
    regimenes = RegimenLaboral.query.filter_by(activo=True).order_by(RegimenLaboral.orden, RegimenLaboral.nombre).all()
    tipos_zafral = TipoZafralCat.query.filter_by(activo=True).order_by(TipoZafralCat.orden, TipoZafralCat.nombre).all()

    # Mapa dep_id -> lista de tareas (para JS)
    tareas_por_dep = {}
    for t in tareas:
        key = str(t.dependencia_id)
        tareas_por_dep.setdefault(key, []).append({'id': t.id, 'nombre': t.nombre})

    return dict(
        dependencias=dependencias,
        tareas=tareas,
        generos=generos,
        estados_civiles=estados_civiles,
        estados_educacion=estados_educacion,
        estados_zafral=estados_zafral,
        regimenes=regimenes,
        tipos_zafral=tipos_zafral,
        tareas_por_dep_json=json.dumps(tareas_por_dep),
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

@admin_bp.route('/funcionarios-zafrales')
@login_required
def zafrales_list():
    q = request.args.get('q', '').strip()
    estado = request.args.get('estado', '')
    dep_id = request.args.get('dep_id', type=int)
    tipo = request.args.get('tipo', '')

    query = FuncionarioZafral.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                FuncionarioZafral.nombres.ilike(like),
                FuncionarioZafral.apellidos.ilike(like),
                FuncionarioZafral.ci.ilike(like),
            )
        )
    if estado:
        query = query.filter(FuncionarioZafral.estado == estado)
    if dep_id:
        query = query.filter(FuncionarioZafral.dependencia_id == dep_id)
    if tipo:
        query = query.filter(FuncionarioZafral.tipo_zafral == tipo)

    zafrales = query.order_by(FuncionarioZafral.apellidos, FuncionarioZafral.nombres).all()
    dependencias = Dependencia.query.order_by(Dependencia.nombre).all()
    estados = EstadoZafralCat.query.filter_by(activo=True).order_by(EstadoZafralCat.orden).all()
    tipos = TipoZafralCat.query.filter_by(activo=True).order_by(TipoZafralCat.orden).all()

    return render_template(
        'admin/zafrales_list.html',
        zafrales=zafrales,
        dependencias=dependencias,
        estados=estados,
        tipos=tipos,
        q=q,
        estado_sel=estado,
        dep_id_sel=dep_id,
        tipo_sel=tipo,
    )


# ---------------------------------------------------------------------------
# Crear
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios-zafrales/nuevo', methods=['GET', 'POST'])
@login_required
def zafrales_nuevo():
    if request.method == 'POST':
        data = request.form
        ci = (data.get('ci') or '').strip()
        nombres = (data.get('nombres') or '').strip()
        apellidos = (data.get('apellidos') or '').strip()
        genero = data.get('genero') or ''
        dependencia_id = data.get('dependencia_id', type=int)
        tarea_id = data.get('tarea_id', type=int)
        tipo_zafral = data.get('tipo_zafral') or 'Zafral Municipal'
        fecha_ingreso_str = data.get('fecha_ingreso', '')
        regimen_laboral = data.get('regimen_laboral') or 'Full Time'
        estado = data.get('estado') or 'Activo'

        errors = []
        if not ci:
            errors.append('La cédula es obligatoria.')
        elif FuncionarioZafral.query.filter_by(ci=ci).first():
            errors.append(f'Ya existe un funcionario zafral con CI {ci}.')
        if not nombres:
            errors.append('Los nombres son obligatorios.')
        if not apellidos:
            errors.append('Los apellidos son obligatorios.')
        if not genero:
            errors.append('El género es obligatorio.')
        if not dependencia_id:
            errors.append('La dependencia es obligatoria.')
        if not tarea_id:
            errors.append('La tarea es obligatoria.')
        if not fecha_ingreso_str:
            errors.append('La fecha de ingreso es obligatoria.')

        fecha_ingreso = _parse_date(fecha_ingreso_str)
        if fecha_ingreso_str and fecha_ingreso is None:
            errors.append('Formato de fecha inválido (use AAAA-MM-DD).')

        if errors:
            for e in errors:
                flash(e, 'error')
            ctx = _form_context_zafral()
            return render_template('admin/zafrales_form.html', modo='nuevo', form_data=data, **ctx)

        zafral = FuncionarioZafral(
            ci=ci,
            nombres=nombres,
            apellidos=apellidos,
            genero=genero,
            fecha_nacimiento=_parse_date(data.get('fecha_nacimiento')),
            pais_nacimiento=data.get('pais_nacimiento') or None,
            departamento_nacimiento=data.get('departamento_nacimiento') or None,
            estado_civil=data.get('estado_civil') or None,
            dependencia_id=dependencia_id,
            tarea_id=tarea_id,
            tipo_zafral=tipo_zafral,
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
        db.session.add(zafral)
        db.session.commit()
        log_activity('ZAFRAL_CREATE', f'Funcionario zafral creado: {nombres} {apellidos} (CI {ci})')
        flash(f'Funcionario zafral {nombres} {apellidos} creado correctamente.', 'success')
        return redirect(url_for('admin.zafrales_list'))

    ctx = _form_context_zafral()
    return render_template('admin/zafrales_form.html', modo='nuevo', form_data={}, **ctx)


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios-zafrales/<int:zaf_id>/editar', methods=['GET', 'POST'])
@login_required
def zafrales_editar(zaf_id):
    zafral = FuncionarioZafral.query.get_or_404(zaf_id)

    if request.method == 'POST':
        data = request.form
        ci = (data.get('ci') or '').strip()
        nombres = (data.get('nombres') or '').strip()
        apellidos = (data.get('apellidos') or '').strip()
        genero = data.get('genero') or ''
        dependencia_id = data.get('dependencia_id', type=int)
        tarea_id = data.get('tarea_id', type=int)
        tipo_zafral = data.get('tipo_zafral') or 'Zafral Municipal'
        fecha_ingreso_str = data.get('fecha_ingreso', '')
        regimen_laboral = data.get('regimen_laboral') or 'Full Time'
        estado = data.get('estado') or zafral.estado

        errors = []
        if not ci:
            errors.append('La cédula es obligatoria.')
        elif FuncionarioZafral.query.filter(FuncionarioZafral.ci == ci, FuncionarioZafral.id != zaf_id).first():
            errors.append(f'Ya existe otro funcionario zafral con CI {ci}.')
        if not nombres:
            errors.append('Los nombres son obligatorios.')
        if not apellidos:
            errors.append('Los apellidos son obligatorios.')
        if not genero:
            errors.append('El género es obligatorio.')
        if not dependencia_id:
            errors.append('La dependencia es obligatoria.')
        if not tarea_id:
            errors.append('La tarea es obligatoria.')
        if not fecha_ingreso_str:
            errors.append('La fecha de ingreso es obligatoria.')

        fecha_ingreso = _parse_date(fecha_ingreso_str)
        if fecha_ingreso_str and fecha_ingreso is None:
            errors.append('Formato de fecha inválido (use AAAA-MM-DD).')

        if errors:
            for e in errors:
                flash(e, 'error')
            ctx = _form_context_zafral()
            return render_template(
                'admin/zafrales_form.html',
                modo='editar',
                zafral=zafral,
                form_data=data,
                **ctx,
            )

        zafral.ci = ci
        zafral.nombres = nombres
        zafral.apellidos = apellidos
        zafral.genero = genero
        zafral.fecha_nacimiento = _parse_date(data.get('fecha_nacimiento'))
        zafral.pais_nacimiento = data.get('pais_nacimiento') or None
        zafral.departamento_nacimiento = data.get('departamento_nacimiento') or None
        zafral.estado_civil = data.get('estado_civil') or None
        zafral.dependencia_id = dependencia_id
        zafral.tarea_id = tarea_id
        zafral.tipo_zafral = tipo_zafral
        zafral.fecha_ingreso = fecha_ingreso
        zafral.regimen_laboral = regimen_laboral
        zafral.estado = estado
        zafral.motivo_baja = data.get('motivo_baja') or None
        zafral.inasistencias = int(data.get('inasistencias') or 0)
        zafral.telefono = data.get('telefono') or None
        zafral.email = data.get('email') or None
        zafral.otro_contacto = data.get('otro_contacto') or None
        zafral.calle = data.get('calle') or None
        zafral.entre_calles = data.get('entre_calles') or None
        zafral.zona = data.get('zona') or None
        zafral.observaciones = data.get('observaciones') or None
        zafral.educacion_primaria = data.get('educacion_primaria') or None
        zafral.educacion_secundaria = data.get('educacion_secundaria') or None
        zafral.educacion_bachillerato = data.get('educacion_bachillerato') or None
        zafral.educacion_terciaria = data.get('educacion_terciaria') or None
        zafral.otras_capacitaciones = data.get('otras_capacitaciones') or None

        db.session.commit()
        log_activity('ZAFRAL_UPDATE', f'Funcionario zafral editado: {nombres} {apellidos} (CI {ci})')
        flash(f'Funcionario zafral {nombres} {apellidos} actualizado correctamente.', 'success')
        return redirect(url_for('admin.zafrales_list'))

    ctx = _form_context_zafral()
    return render_template(
        'admin/zafrales_form.html',
        modo='editar',
        zafral=zafral,
        form_data={},
        **ctx,
    )


# ---------------------------------------------------------------------------
# Eliminar
# ---------------------------------------------------------------------------

@admin_bp.route('/funcionarios-zafrales/<int:zaf_id>/eliminar', methods=['POST'])
@login_required
def zafrales_eliminar(zaf_id):
    zafral = FuncionarioZafral.query.get_or_404(zaf_id)
    nombre = f'{zafral.nombres} {zafral.apellidos}'
    ci = zafral.ci
    db.session.delete(zafral)
    db.session.commit()
    log_activity('ZAFRAL_DELETE', f'Funcionario zafral eliminado: {nombre} (CI {ci})')
    flash(f'Funcionario zafral {nombre} eliminado correctamente.', 'success')
    return redirect(url_for('admin.zafrales_list'))
