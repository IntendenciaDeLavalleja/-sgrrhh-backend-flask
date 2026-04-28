from datetime import date
import base64
from flask import jsonify, request
from app.extensions import db
from app.utils.logging_helper import log_activity
from app.models.hr import (
    Asistencia,
    Cargo,
    Contrato,
    Dependencia,
    EstadoCivilCat,
    EstadoEducacionCat,
    EstadoFuncionarioCat,
    EstadoZafralCat,
    Funcionario,
    FuncionarioZafral,
    GeneroCat,
    RegimenLaboral,
    Tarea,
    TipoZafralCat,
    TrabajoAnterior,
)
from . import api_bp


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_date(value):
    """Parse ISO date string to date object, or return None."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Dependencias
# ---------------------------------------------------------------------------

@api_bp.route('/hr/dependencias', methods=['GET'])
def hr_list_dependencias():
    return jsonify([d.to_dict() for d in Dependencia.query.order_by(Dependencia.nombre).all()])


@api_bp.route('/hr/dependencias', methods=['POST'])
def hr_create_dependencia():
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'nombre requerido'}), 400
    dep = Dependencia(nombre=nombre)
    db.session.add(dep)
    db.session.commit()
    log_activity("API_DEPENDENCIA_CREATE", f"Dependencia creada: '{dep.nombre}' (id={dep.id})")
    return jsonify(dep.to_dict()), 201


@api_bp.route('/hr/dependencias/<int:dep_id>', methods=['PUT'])
def hr_update_dependencia(dep_id):
    dep = Dependencia.query.get_or_404(dep_id)
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'nombre requerido'}), 400
    dep.nombre = nombre
    db.session.commit()
    log_activity("API_DEPENDENCIA_UPDATE", f"Dependencia actualizada: '{dep.nombre}' (id={dep.id})")
    return jsonify(dep.to_dict())


@api_bp.route('/hr/dependencias/<int:dep_id>', methods=['DELETE'])
def hr_delete_dependencia(dep_id):
    dep = Dependencia.query.get_or_404(dep_id)
    nombre = dep.nombre
    db.session.delete(dep)
    db.session.commit()
    log_activity("API_DEPENDENCIA_DELETE", f"Dependencia eliminada: '{nombre}' (id={dep_id})")
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Cargos
# ---------------------------------------------------------------------------

@api_bp.route('/hr/cargos', methods=['GET'])
def hr_list_cargos():
    return jsonify([c.to_dict() for c in Cargo.query.order_by(Cargo.nombre).all()])


@api_bp.route('/hr/cargos', methods=['POST'])
def hr_create_cargo():
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    dependencia_id = data.get('dependenciaId')
    if not nombre or not dependencia_id:
        return jsonify({'error': 'nombre y dependenciaId requeridos'}), 400
    cargo = Cargo(nombre=nombre, dependencia_id=int(dependencia_id))
    db.session.add(cargo)
    db.session.commit()
    log_activity("API_CARGO_CREATE", f"Cargo creado: '{cargo.nombre}' (id={cargo.id})")
    return jsonify(cargo.to_dict()), 201


@api_bp.route('/hr/cargos/<int:cargo_id>', methods=['PUT'])
def hr_update_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    data = request.get_json(silent=True) or {}
    if 'nombre' in data:
        cargo.nombre = data['nombre'].strip()
    if 'dependenciaId' in data:
        cargo.dependencia_id = int(data['dependenciaId'])
    db.session.commit()
    log_activity("API_CARGO_UPDATE", f"Cargo actualizado: '{cargo.nombre}' (id={cargo.id})")
    return jsonify(cargo.to_dict())


@api_bp.route('/hr/cargos/<int:cargo_id>', methods=['DELETE'])
def hr_delete_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    nombre = cargo.nombre
    db.session.delete(cargo)
    db.session.commit()
    log_activity("API_CARGO_DELETE", f"Cargo eliminado: '{nombre}' (id={cargo_id})")
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Funcionarios
# ---------------------------------------------------------------------------

@api_bp.route('/hr/funcionarios', methods=['GET'])
def hr_list_funcionarios():
    search = request.args.get('search', '').strip().lower()
    estado = request.args.get('estado', '').strip()
    dependencia_id = request.args.get('dependenciaId', '').strip()
    page = int(request.args.get('page', 0))
    page_size = int(request.args.get('pageSize', 8))

    query = Funcionario.query

    if search:
        pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                db.func.lower(Funcionario.nombres).like(pattern),
                db.func.lower(Funcionario.apellidos).like(pattern),
                db.func.lower(Funcionario.ci).like(pattern),
            )
        )
    if estado:
        query = query.filter(Funcionario.estado == estado)
    if dependencia_id:
        query = query.filter(Funcionario.dependencia_id == int(dependencia_id))

    total = query.count()
    funcionarios = query.order_by(Funcionario.apellidos, Funcionario.nombres).offset(page * page_size).limit(page_size).all()

    return jsonify({
        'data': [f.to_dict(include_trabajos=False) for f in funcionarios],
        'total': total,
    })


@api_bp.route('/hr/funcionarios', methods=['POST'])
def hr_create_funcionario():
    data = request.get_json(silent=True) or {}
    errors = []
    for field in ('ci', 'nombres', 'apellidos', 'genero', 'dependenciaId', 'cargoId', 'fechaIngreso', 'regimenLaboral', 'estado'):
        if not data.get(field):
            errors.append(field)
    if errors:
        return jsonify({'error': f'Campos requeridos: {", ".join(errors)}'}), 400

    funcionario = Funcionario(
        ci=data['ci'].strip(),
        nombres=data['nombres'].strip(),
        apellidos=data['apellidos'].strip(),
        genero=data['genero'],
        fecha_nacimiento=_parse_date(data.get('fechaNacimiento')),
        pais_nacimiento=data.get('paisNacimiento'),
        departamento_nacimiento=data.get('departamentoNacimiento'),
        estado_civil=data.get('estadoCivil'),
        dependencia_id=int(data['dependenciaId']),
        cargo_id=int(data['cargoId']),
        fecha_ingreso=_parse_date(data['fechaIngreso']),
        regimen_laboral=data['regimenLaboral'],
        estado=data['estado'],
        motivo_baja=data.get('motivoBaja'),
        inasistencias=int(data.get('inasistencias', 0)),
        telefono=data.get('telefono'),
        email=data.get('email'),
        otro_contacto=data.get('otroContacto'),
        calle=data.get('calle'),
        entre_calles=data.get('entreCalles'),
        zona=data.get('zona'),
        observaciones=data.get('observaciones'),
        educacion_primaria=data.get('educacionPrimaria'),
        educacion_secundaria=data.get('educacionSecundaria'),
        educacion_bachillerato=data.get('educacionBachillerato'),
        educacion_terciaria=data.get('educacionTerciaria'),
        otras_capacitaciones=data.get('otrasCapacitaciones'),
    )
    db.session.add(funcionario)
    db.session.flush()  # get funcionario.id before creating trabajos

    for ta in data.get('trabajosAnteriores', []):
        if ta.get('empresa'):
            db.session.add(TrabajoAnterior(
                funcionario_id=funcionario.id,
                empresa=ta['empresa'],
                periodo=ta.get('periodo'),
                seccion=ta.get('seccion'),
                cargo=ta.get('cargo'),
            ))

    db.session.commit()
    log_activity("API_FUNCIONARIO_CREATE", f"Funcionario creado: {funcionario.nombres} {funcionario.apellidos}, CI={funcionario.ci} (id={funcionario.id})")
    return jsonify(funcionario.to_dict()), 201


@api_bp.route('/hr/funcionarios/<int:fun_id>', methods=['GET'])
def hr_get_funcionario(fun_id):
    f = Funcionario.query.get_or_404(fun_id)
    return jsonify(f.to_dict())


@api_bp.route('/hr/funcionarios/<int:fun_id>', methods=['PUT'])
def hr_update_funcionario(fun_id):
    f = Funcionario.query.get_or_404(fun_id)
    data = request.get_json(silent=True) or {}

    field_map = {
        'ci': 'ci', 'nombres': 'nombres', 'apellidos': 'apellidos',
        'genero': 'genero', 'paisNacimiento': 'pais_nacimiento',
        'departamentoNacimiento': 'departamento_nacimiento',
        'estadoCivil': 'estado_civil', 'regimenLaboral': 'regimen_laboral',
        'estado': 'estado', 'motivoBaja': 'motivo_baja',
        'telefono': 'telefono', 'email': 'email', 'otroContacto': 'otro_contacto',
        'calle': 'calle', 'entreCalles': 'entre_calles', 'zona': 'zona',
        'observaciones': 'observaciones', 'educacionPrimaria': 'educacion_primaria',
        'educacionSecundaria': 'educacion_secundaria',
        'educacionBachillerato': 'educacion_bachillerato',
        'educacionTerciaria': 'educacion_terciaria',
        'otrasCapacitaciones': 'otras_capacitaciones',
    }
    for camel, snake in field_map.items():
        if camel in data:
            setattr(f, snake, data[camel])

    if 'inasistencias' in data:
        f.inasistencias = int(data['inasistencias'])
    if 'dependenciaId' in data:
        f.dependencia_id = int(data['dependenciaId'])
    if 'cargoId' in data:
        f.cargo_id = int(data['cargoId'])
    if 'fechaNacimiento' in data:
        f.fecha_nacimiento = _parse_date(data['fechaNacimiento'])
    if 'fechaIngreso' in data:
        f.fecha_ingreso = _parse_date(data['fechaIngreso'])

    if 'trabajosAnteriores' in data:
        TrabajoAnterior.query.filter_by(funcionario_id=f.id).delete()
        for ta in data['trabajosAnteriores']:
            if ta.get('empresa'):
                db.session.add(TrabajoAnterior(
                    funcionario_id=f.id,
                    empresa=ta['empresa'],
                    periodo=ta.get('periodo'),
                    seccion=ta.get('seccion'),
                    cargo=ta.get('cargo'),
                ))

    db.session.commit()
    log_activity("API_FUNCIONARIO_UPDATE", f"Funcionario actualizado: {f.nombres} {f.apellidos}, CI={f.ci} (id={f.id})")
    return jsonify(f.to_dict())


@api_bp.route('/hr/funcionarios/<int:fun_id>', methods=['DELETE'])
def hr_delete_funcionario(fun_id):
    f = Funcionario.query.get_or_404(fun_id)
    desc = f"{f.nombres} {f.apellidos}, CI={f.ci}"
    db.session.delete(f)
    db.session.commit()
    log_activity("API_FUNCIONARIO_DELETE", f"Funcionario eliminado: {desc} (id={fun_id})")
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Contratos
# ---------------------------------------------------------------------------

@api_bp.route('/hr/contratos', methods=['GET'])
def hr_list_contratos():
    contratos = Contrato.query.order_by(Contrato.fecha_inicio.desc()).all()
    return jsonify([c.to_dict() for c in contratos])


@api_bp.route('/hr/contratos/<int:con_id>/pdf', methods=['GET'])
def hr_get_contrato_pdf(con_id):
    from app.services.minio_service import minio_service
    c = Contrato.query.get_or_404(con_id)
    if not c.documento_key:
        return jsonify({'error': 'Sin documento adjunto'}), 404
    if not minio_service.available:
        return jsonify({'error': 'Almacenamiento no disponible'}), 503
    url = minio_service.presigned_get(c.documento_key, expires_seconds=300)
    return jsonify({'url': url})


@api_bp.route('/hr/contratos/<int:con_id>/pdf', methods=['DELETE'])
def hr_delete_contrato_pdf(con_id):
    from app.services.minio_service import minio_service
    c = Contrato.query.get_or_404(con_id)
    if not c.documento_key:
        return jsonify({'error': 'Sin documento adjunto'}), 404
    if not minio_service.available:
        return jsonify({'error': 'Almacenamiento no disponible'}), 503
    try:
        minio_service.delete(c.documento_key)
    except Exception as exc:
        return jsonify({'error': f'No se pudo eliminar de MinIO: {exc}'}), 500
    c.documento_key = None
    db.session.commit()
    log_activity("API_CONTRATO_PDF_DELETE", f"PDF eliminado del contrato id={con_id}")
    return jsonify({'ok': True})


@api_bp.route('/hr/contratos/funcionario/<int:fun_id>', methods=['GET'])
def hr_contratos_by_funcionario(fun_id):
    contratos = Contrato.query.filter_by(funcionario_id=fun_id).order_by(Contrato.fecha_inicio.desc()).all()
    return jsonify([c.to_dict() for c in contratos])


@api_bp.route('/hr/contratos', methods=['POST'])
def hr_create_contrato():
    from app.services.minio_service import minio_service
    data = request.get_json(silent=True) or {}
    for field in ('funcionarioId', 'tipo', 'fechaInicio', 'fechaFin', 'estado'):
        if not data.get(field):
            return jsonify({'error': f'{field} requerido'}), 400

    documento_key = None
    pdf_b64 = data.get('documentoBase64')
    if pdf_b64:
        if not minio_service.available:
            return jsonify({'error': 'Almacenamiento no disponible, no se puede subir el PDF'}), 503
        try:
            pdf_bytes = base64.b64decode(pdf_b64)
            documento_key = minio_service.upload_pdf(pdf_bytes, prefix='contratos')
        except Exception as exc:
            return jsonify({'error': f'Error al subir PDF: {exc}'}), 500

    contrato = Contrato(
        funcionario_id=int(data['funcionarioId']),
        tipo=data['tipo'],
        fecha_inicio=_parse_date(data['fechaInicio']),
        fecha_fin=_parse_date(data['fechaFin']),
        estado=data['estado'],
        sueldo_nominal=data.get('sueldoNominal'),
        observaciones=data.get('observaciones'),
        documento_key=documento_key,
    )
    db.session.add(contrato)
    db.session.commit()
    log_activity("API_CONTRATO_CREATE", f"Contrato creado: tipo='{contrato.tipo}', estado='{contrato.estado}', funcionario_id={contrato.funcionario_id} (id={contrato.id})")
    return jsonify(contrato.to_dict()), 201


@api_bp.route('/hr/contratos/<int:con_id>', methods=['PUT'])
def hr_update_contrato(con_id):
    from app.services.minio_service import minio_service
    c = Contrato.query.get_or_404(con_id)
    data = request.get_json(silent=True) or {}

    if 'tipo' in data:
        c.tipo = data['tipo']
    if 'estado' in data:
        c.estado = data['estado']
    if 'fechaInicio' in data:
        c.fecha_inicio = _parse_date(data['fechaInicio'])
    if 'fechaFin' in data:
        c.fecha_fin = _parse_date(data['fechaFin'])
    if 'sueldoNominal' in data:
        c.sueldo_nominal = data['sueldoNominal']
    if 'observaciones' in data:
        c.observaciones = data['observaciones']
    if 'funcionarioId' in data:
        c.funcionario_id = int(data['funcionarioId'])
    if 'documentoBase64' in data:
        pdf_b64 = data['documentoBase64']
        if pdf_b64:
            if not minio_service.available:
                return jsonify({'error': 'Almacenamiento no disponible'}), 503
            try:
                # Delete old file if exists
                if c.documento_key:
                    try:
                        minio_service.delete(c.documento_key)
                    except Exception:
                        pass
                pdf_bytes = base64.b64decode(pdf_b64)
                c.documento_key = minio_service.upload_pdf(pdf_bytes, prefix='contratos')
            except Exception as exc:
                return jsonify({'error': f'Error al subir PDF: {exc}'}), 500
        else:
            c.documento_key = None

    db.session.commit()
    log_activity("API_CONTRATO_UPDATE", f"Contrato actualizado: tipo='{c.tipo}', estado='{c.estado}' (id={c.id})")
    return jsonify(c.to_dict())


@api_bp.route('/hr/contratos/<int:con_id>', methods=['DELETE'])
def hr_delete_contrato(con_id):
    from app.services.minio_service import minio_service
    c = Contrato.query.get_or_404(con_id)
    # Clean up attached PDF from MinIO before deleting record
    if c.documento_key and minio_service.available:
        try:
            minio_service.delete(c.documento_key)
        except Exception:
            pass
    desc = f"tipo='{c.tipo}', funcionario_id={c.funcionario_id}"
    db.session.delete(c)
    db.session.commit()
    log_activity("API_CONTRATO_DELETE", f"Contrato eliminado: {desc} (id={con_id})")
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Asistencias
# ---------------------------------------------------------------------------

@api_bp.route('/hr/asistencias', methods=['GET'])
def hr_list_asistencias():
    asistencias = Asistencia.query.order_by(Asistencia.fecha.desc()).all()
    return jsonify([a.to_dict() for a in asistencias])


@api_bp.route('/hr/asistencias/funcionario/<int:fun_id>', methods=['GET'])
def hr_asistencias_by_funcionario(fun_id):
    asistencias = Asistencia.query.filter_by(funcionario_id=fun_id).order_by(Asistencia.fecha.desc()).all()
    return jsonify([a.to_dict() for a in asistencias])


@api_bp.route('/hr/asistencias', methods=['POST'])
def hr_create_asistencia():
    data = request.get_json(silent=True) or {}
    for field in ('funcionarioId', 'fecha', 'estado'):
        if not data.get(field):
            return jsonify({'error': f'{field} requerido'}), 400

    asistencia = Asistencia(
        funcionario_id=int(data['funcionarioId']),
        fecha=_parse_date(data['fecha']),
        estado=data['estado'],
        observaciones=data.get('observaciones'),
    )
    db.session.add(asistencia)
    db.session.commit()
    log_activity("API_ASISTENCIA_CREATE", f"Asistencia registrada: funcionario_id={asistencia.funcionario_id}, fecha={asistencia.fecha}, estado='{asistencia.estado}' (id={asistencia.id})")
    return jsonify(asistencia.to_dict()), 201


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@api_bp.route('/hr/dashboard', methods=['GET'])
def hr_dashboard():
    from datetime import datetime
    now = datetime.utcnow()
    primer_dia_mes = now.replace(day=1).date()

    total_funcionarios = Funcionario.query.count()
    zafrales_activos = FuncionarioZafral.query.filter_by(estado='Activo').count()
    contratos_por_vencer = Contrato.query.filter_by(estado='Por vencer').count()
    inasistencias_mes = Asistencia.query.filter(
        Asistencia.estado == 'Falta',
        Asistencia.fecha >= primer_dia_mes,
    ).count()

    return jsonify({
        'totalFuncionarios': total_funcionarios,
        'zafralesActivos': zafrales_activos,
        'contratosPorVencer': contratos_por_vencer,
        'inasistenciasMes': inasistencias_mes,
    })


# ---------------------------------------------------------------------------
# Tareas (para Funcionarios Zafrales)
# ---------------------------------------------------------------------------

@api_bp.route('/hr/tareas', methods=['GET'])
def hr_list_tareas():
    return jsonify([t.to_dict() for t in Tarea.query.order_by(Tarea.nombre).all()])


@api_bp.route('/hr/tareas', methods=['POST'])
def hr_create_tarea():
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    dependencia_id = data.get('dependenciaId')
    if not nombre or not dependencia_id:
        return jsonify({'error': 'nombre y dependenciaId requeridos'}), 400
    tarea = Tarea(nombre=nombre, dependencia_id=int(dependencia_id))
    db.session.add(tarea)
    db.session.commit()
    log_activity("API_TAREA_CREATE", f"Tarea creada: '{tarea.nombre}' (id={tarea.id})")
    return jsonify(tarea.to_dict()), 201


@api_bp.route('/hr/tareas/<int:tarea_id>', methods=['PUT'])
def hr_update_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    data = request.get_json(silent=True) or {}
    if 'nombre' in data:
        tarea.nombre = data['nombre'].strip()
    if 'dependenciaId' in data:
        tarea.dependencia_id = int(data['dependenciaId'])
    db.session.commit()
    log_activity("API_TAREA_UPDATE", f"Tarea actualizada: '{tarea.nombre}' (id={tarea.id})")
    return jsonify(tarea.to_dict())


@api_bp.route('/hr/tareas/<int:tarea_id>', methods=['DELETE'])
def hr_delete_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    nombre = tarea.nombre
    db.session.delete(tarea)
    db.session.commit()
    log_activity("API_TAREA_DELETE", f"Tarea eliminada: '{nombre}' (id={tarea_id})")
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Funcionarios Zafrales
# ---------------------------------------------------------------------------

@api_bp.route('/hr/funcionarios-zafrales', methods=['GET'])
def hr_list_funcionarios_zafrales():
    search = request.args.get('search', '').strip().lower()
    estado = request.args.get('estado', '').strip()
    tipo_zafral = request.args.get('tipoZafral', '').strip()
    dependencia_id = request.args.get('dependenciaId', '').strip()
    page = int(request.args.get('page', 0))
    page_size = int(request.args.get('pageSize', 8))

    query = FuncionarioZafral.query

    if search:
        pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                db.func.lower(FuncionarioZafral.nombres).like(pattern),
                db.func.lower(FuncionarioZafral.apellidos).like(pattern),
                db.func.lower(FuncionarioZafral.ci).like(pattern),
            )
        )
    if estado:
        query = query.filter(FuncionarioZafral.estado == estado)
    if tipo_zafral:
        query = query.filter(FuncionarioZafral.tipo_zafral == tipo_zafral)
    if dependencia_id:
        query = query.filter(FuncionarioZafral.dependencia_id == int(dependencia_id))

    total = query.count()
    funcionarios = (
        query.order_by(FuncionarioZafral.apellidos, FuncionarioZafral.nombres)
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    return jsonify({
        'data': [f.to_dict() for f in funcionarios],
        'total': total,
    })


@api_bp.route('/hr/funcionarios-zafrales', methods=['POST'])
def hr_create_funcionario_zafral():
    data = request.get_json(silent=True) or {}
    required = ('ci', 'nombres', 'apellidos', 'genero', 'dependenciaId', 'tareaId', 'tipoZafral', 'fechaIngreso', 'regimenLaboral', 'estado')
    errors = [f for f in required if not data.get(f)]
    if errors:
        return jsonify({'error': f'Campos requeridos: {", ".join(errors)}'}), 400

    fz = FuncionarioZafral(
        ci=data['ci'].strip(),
        nombres=data['nombres'].strip(),
        apellidos=data['apellidos'].strip(),
        genero=data['genero'],
        fecha_nacimiento=_parse_date(data.get('fechaNacimiento')),
        pais_nacimiento=data.get('paisNacimiento'),
        departamento_nacimiento=data.get('departamentoNacimiento'),
        estado_civil=data.get('estadoCivil'),
        dependencia_id=int(data['dependenciaId']),
        tarea_id=int(data['tareaId']),
        tipo_zafral=data['tipoZafral'],
        fecha_ingreso=_parse_date(data['fechaIngreso']),
        regimen_laboral=data['regimenLaboral'],
        estado=data['estado'],
        motivo_baja=data.get('motivoBaja'),
        inasistencias=int(data.get('inasistencias', 0)),
        telefono=data.get('telefono'),
        email=data.get('email'),
        otro_contacto=data.get('otroContacto'),
        calle=data.get('calle'),
        entre_calles=data.get('entreCalles'),
        zona=data.get('zona'),
        observaciones=data.get('observaciones'),
        educacion_primaria=data.get('educacionPrimaria'),
        educacion_secundaria=data.get('educacionSecundaria'),
        educacion_bachillerato=data.get('educacionBachillerato'),
        educacion_terciaria=data.get('educacionTerciaria'),
        otras_capacitaciones=data.get('otrasCapacitaciones'),
    )
    db.session.add(fz)
    db.session.commit()
    log_activity("API_FZ_CREATE", f"Funcionario zafral creado: {fz.nombres} {fz.apellidos}, CI={fz.ci} (id={fz.id})")
    return jsonify(fz.to_dict()), 201


@api_bp.route('/hr/funcionarios-zafrales/<int:fz_id>', methods=['GET'])
def hr_get_funcionario_zafral(fz_id):
    fz = FuncionarioZafral.query.get_or_404(fz_id)
    return jsonify(fz.to_dict())


@api_bp.route('/hr/funcionarios-zafrales/<int:fz_id>', methods=['PUT'])
def hr_update_funcionario_zafral(fz_id):
    fz = FuncionarioZafral.query.get_or_404(fz_id)
    data = request.get_json(silent=True) or {}

    field_map = {
        'ci': 'ci', 'nombres': 'nombres', 'apellidos': 'apellidos',
        'genero': 'genero', 'paisNacimiento': 'pais_nacimiento',
        'departamentoNacimiento': 'departamento_nacimiento',
        'estadoCivil': 'estado_civil', 'tipoZafral': 'tipo_zafral',
        'regimenLaboral': 'regimen_laboral', 'estado': 'estado',
        'motivoBaja': 'motivo_baja', 'telefono': 'telefono',
        'email': 'email', 'otroContacto': 'otro_contacto',
        'calle': 'calle', 'entreCalles': 'entre_calles', 'zona': 'zona',
        'observaciones': 'observaciones',
        'educacionPrimaria': 'educacion_primaria',
        'educacionSecundaria': 'educacion_secundaria',
        'educacionBachillerato': 'educacion_bachillerato',
        'educacionTerciaria': 'educacion_terciaria',
        'otrasCapacitaciones': 'otras_capacitaciones',
    }
    for camel, snake in field_map.items():
        if camel in data:
            setattr(fz, snake, data[camel])

    if 'inasistencias' in data:
        fz.inasistencias = int(data['inasistencias'])
    if 'dependenciaId' in data:
        fz.dependencia_id = int(data['dependenciaId'])
    if 'tareaId' in data:
        fz.tarea_id = int(data['tareaId'])
    if 'fechaNacimiento' in data:
        fz.fecha_nacimiento = _parse_date(data['fechaNacimiento'])
    if 'fechaIngreso' in data:
        fz.fecha_ingreso = _parse_date(data['fechaIngreso'])

    db.session.commit()
    log_activity("API_FZ_UPDATE", f"Funcionario zafral actualizado: {fz.nombres} {fz.apellidos}, CI={fz.ci} (id={fz.id})")
    return jsonify(fz.to_dict())


@api_bp.route('/hr/funcionarios-zafrales/<int:fz_id>', methods=['DELETE'])
def hr_delete_funcionario_zafral(fz_id):
    fz = FuncionarioZafral.query.get_or_404(fz_id)
    desc = f"{fz.nombres} {fz.apellidos}, CI={fz.ci}"
    db.session.delete(fz)
    db.session.commit()
    log_activity("API_FZ_DELETE", f"Funcionario zafral eliminado: {desc} (id={fz_id})")
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Opciones (catálogos configurables)
# ---------------------------------------------------------------------------

@api_bp.route('/hr/opciones', methods=['GET'])
def hr_opciones():
    """Devuelve todos los catálogos configurables para los formularios."""

    def names(model):
        return [
            r.nombre
            for r in model.query.filter_by(activo=True)
            .order_by(model.orden, model.nombre)
            .all()
        ]

    return jsonify({
        'regimenesLaborales': names(RegimenLaboral),
        'tiposZafral': names(TipoZafralCat),
        'generos': names(GeneroCat),
        'estadosCiviles': names(EstadoCivilCat),
        'estadosEducacion': names(EstadoEducacionCat),
        'estadosFuncionario': names(EstadoFuncionarioCat),
        'estadosZafral': names(EstadoZafralCat),
    })

