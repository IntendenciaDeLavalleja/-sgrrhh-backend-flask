from datetime import datetime

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models.hr import Contrato, Funcionario, RegimenLaboral
from app.utils.logging_helper import log_activity
from .. import admin_bp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(s):
    if s and s.strip():
        try:
            return datetime.strptime(s.strip(), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def _form_context():
    """Contexto compartido para formularios de contrato."""
    return dict(
        funcionarios=Funcionario.query.order_by(Funcionario.apellidos, Funcionario.nombres).all(),
        regimenes=RegimenLaboral.query.filter_by(activo=True).order_by(RegimenLaboral.orden, RegimenLaboral.nombre).all(),
    )


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------

@admin_bp.route('/contratos')
@login_required
def contratos_list():
    q = request.args.get('q', '').strip()
    estado = request.args.get('estado', '').strip()
    regimen_id = request.args.get('regimen_id', type=int)

    query = Contrato.query.join(Funcionario).join(RegimenLaboral)
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
        query = query.filter(Contrato.estado == estado)
    if regimen_id:
        query = query.filter(Contrato.regimen_laboral_id == regimen_id)

    contratos = query.order_by(Contrato.fecha_inicio.desc()).all()
    regimenes = RegimenLaboral.query.filter_by(activo=True).order_by(RegimenLaboral.orden).all()
    estados = ['Vigente', 'Por vencer', 'Vencido', 'Rescindido']

    return render_template(
        'admin/contratos_list.html',
        contratos=contratos,
        regimenes=regimenes,
        estados=estados,
        q=q,
        estado_sel=estado,
        regimen_id_sel=regimen_id,
    )


# ---------------------------------------------------------------------------
# Crear
# ---------------------------------------------------------------------------

@admin_bp.route('/contratos/nuevo', methods=['GET', 'POST'])
@login_required
def contratos_nuevo():
    if request.method == 'POST':
        data = request.form
        funcionario_id = data.get('funcionario_id', type=int)
        regimen_laboral_id = data.get('regimen_laboral_id', type=int)
        fecha_fin_str = data.get('fecha_fin', '')
        estado = data.get('estado') or 'Vigente'
        sueldo_nominal = data.get('sueldo_nominal', type=float)
        observaciones = data.get('observaciones', '')

        errors = []
        funcionario = Funcionario.query.get(funcionario_id) if funcionario_id else None
        if not funcionario:
            errors.append('El funcionario es obligatorio.')
        regimen = RegimenLaboral.query.get(regimen_laboral_id) if regimen_laboral_id else None
        if not regimen:
            errors.append('El régimen laboral es obligatorio.')

        fecha_inicio = funcionario.fecha_ingreso if funcionario else None
        if not fecha_inicio:
            errors.append('El funcionario seleccionado no tiene fecha de ingreso.')

        fecha_fin = _parse_date(fecha_fin_str)
        if fecha_fin_str and fecha_fin is None:
            errors.append('Formato de fecha de fin inválido (use AAAA-MM-DD).')
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errors.append('La fecha de fin no puede ser anterior a la fecha de inicio.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('admin/contratos_form.html', modo='nuevo', form_data=data, **_form_context())

        contrato = Contrato(
            funcionario_id=funcionario.id,
            regimen_laboral_id=regimen.id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado,
            sueldo_nominal=sueldo_nominal,
            observaciones=observaciones or None,
        )
        db.session.add(contrato)
        db.session.commit()
        log_activity('CONTRATO_CREATE', f'Contrato creado: {regimen.nombre} para {funcionario.nombres} {funcionario.apellidos} (id={contrato.id})')
        flash('Contrato creado correctamente.', 'success')
        return redirect(url_for('admin.contratos_list'))

    return render_template('admin/contratos_form.html', modo='nuevo', form_data={}, **_form_context())


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------

@admin_bp.route('/contratos/<int:con_id>/editar', methods=['GET', 'POST'])
@login_required
def contratos_editar(con_id):
    contrato = Contrato.query.get_or_404(con_id)

    if request.method == 'POST':
        data = request.form
        funcionario_id = data.get('funcionario_id', type=int)
        regimen_laboral_id = data.get('regimen_laboral_id', type=int)
        fecha_fin_str = data.get('fecha_fin', '')
        estado = data.get('estado') or contrato.estado
        sueldo_nominal = data.get('sueldo_nominal', type=float)
        observaciones = data.get('observaciones', '')

        errors = []
        funcionario = Funcionario.query.get(funcionario_id) if funcionario_id else None
        if not funcionario:
            errors.append('El funcionario es obligatorio.')
        regimen = RegimenLaboral.query.get(regimen_laboral_id) if regimen_laboral_id else None
        if not regimen:
            errors.append('El régimen laboral es obligatorio.')

        fecha_inicio = funcionario.fecha_ingreso if funcionario else None
        if not fecha_inicio:
            errors.append('El funcionario seleccionado no tiene fecha de ingreso.')

        fecha_fin = _parse_date(fecha_fin_str)
        if fecha_fin_str and fecha_fin is None:
            errors.append('Formato de fecha de fin inválido (use AAAA-MM-DD).')
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errors.append('La fecha de fin no puede ser anterior a la fecha de inicio.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template(
                'admin/contratos_form.html',
                modo='editar',
                contrato=contrato,
                form_data=data,
                **_form_context(),
            )

        contrato.funcionario_id = funcionario.id
        contrato.regimen_laboral_id = regimen.id
        contrato.fecha_inicio = fecha_inicio
        contrato.fecha_fin = fecha_fin
        contrato.estado = estado
        contrato.sueldo_nominal = sueldo_nominal
        contrato.observaciones = observaciones or None

        db.session.commit()
        log_activity('CONTRATO_UPDATE', f'Contrato actualizado: {regimen.nombre} para {funcionario.nombres} {funcionario.apellidos} (id={contrato.id})')
        flash('Contrato actualizado correctamente.', 'success')
        return redirect(url_for('admin.contratos_list'))

    form_data = {
        'funcionario_id': contrato.funcionario_id,
        'regimen_laboral_id': contrato.regimen_laboral_id,
        'fecha_fin': contrato.fecha_fin.isoformat() if contrato.fecha_fin else '',
        'estado': contrato.estado,
        'sueldo_nominal': float(contrato.sueldo_nominal) if contrato.sueldo_nominal is not None else '',
        'observaciones': contrato.observaciones or '',
    }
    return render_template(
        'admin/contratos_form.html',
        modo='editar',
        contrato=contrato,
        form_data=form_data,
        **_form_context(),
    )


# ---------------------------------------------------------------------------
# Eliminar
# ---------------------------------------------------------------------------

@admin_bp.route('/contratos/<int:con_id>/eliminar', methods=['POST'])
@login_required
def contratos_eliminar(con_id):
    contrato = Contrato.query.get_or_404(con_id)
    from app.services.minio_service import minio_service
    if contrato.documento_key and minio_service.available:
        try:
            minio_service.delete(contrato.documento_key)
        except Exception:
            pass
    desc = f"Contrato id={contrato.id}, funcionario_id={contrato.funcionario_id}"
    db.session.delete(contrato)
    db.session.commit()
    log_activity('CONTRATO_DELETE', f'{desc} eliminado')
    flash('Contrato eliminado correctamente.', 'success')
    return redirect(url_for('admin.contratos_list'))
