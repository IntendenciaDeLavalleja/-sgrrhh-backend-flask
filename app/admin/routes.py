from datetime import datetime
from flask import render_template
from flask_login import login_required
from app.models.hr import Funcionario, FuncionarioZafral, Contrato, Asistencia
from . import admin_bp

from .routes_components import auth  # noqa: F401
from .routes_components import audit  # noqa: F401
from .routes_components import hr  # noqa: F401
from .routes_components import funcionarios  # noqa: F401
from .routes_components import zafrales  # noqa: F401
from .routes_components import usuarios  # noqa: F401


@admin_bp.route('/')
@login_required
def dashboard():
    now = datetime.utcnow()
    primer_dia_mes = now.replace(day=1).date()

    total_funcionarios = Funcionario.query.count()
    zafrales_activos = FuncionarioZafral.query.filter_by(estado='Activo').count()
    contratos_por_vencer = Contrato.query.filter_by(estado='Por vencer').count()
    inasistencias_mes = Asistencia.query.filter(
        Asistencia.estado == 'Falta',
        Asistencia.fecha >= primer_dia_mes,
    ).count()

    return render_template(
        'admin/dashboard.html',
        total_funcionarios=total_funcionarios,
        zafrales_activos=zafrales_activos,
        contratos_por_vencer=contratos_por_vencer,
        inasistencias_mes=inasistencias_mes,
    )
