from datetime import datetime
from app.extensions import db


class Dependencia(db.Model):
    __tablename__ = 'hr_dependencias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    funcionarios = db.relationship('Funcionario', backref='dependencia', lazy='dynamic')
    funcionarios_zafrales = db.relationship('FuncionarioZafral', backref='dependencia', lazy='dynamic')

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class Cargo(db.Model):
    __tablename__ = 'hr_cargos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    funcionarios = db.relationship('Funcionario', backref='cargo', lazy='dynamic')

    def to_dict(self):
        return {
            'id': str(self.id),
            'nombre': self.nombre,
        }


class Funcionario(db.Model):
    __tablename__ = 'hr_funcionarios'

    id = db.Column(db.Integer, primary_key=True)
    ci = db.Column(db.String(30), unique=True, nullable=False)
    nombres = db.Column(db.String(150), nullable=False)
    apellidos = db.Column(db.String(150), nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    pais_nacimiento = db.Column(db.String(100), nullable=True)
    departamento_nacimiento = db.Column(db.String(100), nullable=True)
    estado_civil = db.Column(db.String(30), nullable=True)

    dependencia_id = db.Column(db.Integer, db.ForeignKey('hr_dependencias.id'), nullable=False)
    cargo_id = db.Column(db.Integer, db.ForeignKey('hr_cargos.id'), nullable=False)

    fecha_ingreso = db.Column(db.Date, nullable=False)
    regimen_laboral = db.Column(db.String(30), nullable=False, default='Full Time')
    estado = db.Column(db.String(30), nullable=False, default='Presupuestado')
    motivo_baja = db.Column(db.String(255), nullable=True)
    inasistencias = db.Column(db.Integer, default=0)

    telefono = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    otro_contacto = db.Column(db.String(150), nullable=True)
    calle = db.Column(db.String(200), nullable=True)
    entre_calles = db.Column(db.String(200), nullable=True)
    zona = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    nivel_educativo = db.Column(db.String(100), nullable=True)
    otras_capacitaciones = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contratos = db.relationship(
        'Contrato', backref='funcionario', lazy='dynamic', cascade='all, delete-orphan'
    )
    asistencias = db.relationship(
        'Asistencia', backref='funcionario', lazy='dynamic', cascade='all, delete-orphan'
    )
    trabajos_anteriores = db.relationship(
        'TrabajoAnterior', backref='funcionario', lazy='dynamic', cascade='all, delete-orphan'
    )

    def to_dict(self, include_trabajos=True):
        return {
            'id': str(self.id),
            'ci': self.ci,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'genero': self.genero,
            'fechaNacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'paisNacimiento': self.pais_nacimiento,
            'departamentoNacimiento': self.departamento_nacimiento,
            'estadoCivil': self.estado_civil,
            'dependenciaId': str(self.dependencia_id),
            'cargoId': str(self.cargo_id),
            'fechaIngreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            'regimenLaboral': self.regimen_laboral,
            'estado': self.estado,
            'motivoBaja': self.motivo_baja,
            'inasistencias': self.inasistencias,
            'telefono': self.telefono,
            'email': self.email,
            'otroContacto': self.otro_contacto,
            'calle': self.calle,
            'entreCalles': self.entre_calles,
            'zona': self.zona,
            'observaciones': self.observaciones,
            'nivelEducativo': self.nivel_educativo,
            'otrasCapacitaciones': self.otras_capacitaciones,
            'trabajosAnteriores': (
                [t.to_dict() for t in self.trabajos_anteriores.all()]
                if include_trabajos
                else []
            ),
        }


class TrabajoAnterior(db.Model):
    __tablename__ = 'hr_trabajos_anteriores'

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('hr_funcionarios.id'), nullable=False)
    empresa = db.Column(db.String(200), nullable=False)
    periodo = db.Column(db.String(100), nullable=True)
    seccion = db.Column(db.String(150), nullable=True)
    cargo = db.Column(db.String(150), nullable=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'empresa': self.empresa,
            'periodo': self.periodo,
            'seccion': self.seccion,
            'cargo': self.cargo,
        }


class Contrato(db.Model):
    __tablename__ = 'hr_contratos'

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('hr_funcionarios.id'), nullable=True)
    funcionario_zafral_id = db.Column(db.Integer, db.ForeignKey('hr_funcionarios_zafrales.id'), nullable=True)
    # Tipo de contrato vinculado al catálogo de regímenes laborales
    regimen_laboral_id = db.Column(db.Integer, db.ForeignKey('hr_regimenes_laborales.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(30), nullable=False, default='Vigente')
    sueldo_nominal = db.Column(db.Numeric(12, 2), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    documento_key = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    regimen_laboral = db.relationship('RegimenLaboral', backref='contratos')
    funcionario_zafral = db.relationship('FuncionarioZafral', backref='contratos')

    def to_dict(self):
        return {
            'id': str(self.id),
            'funcionarioId': str(self.funcionario_id) if self.funcionario_id else None,
            'funcionarioZafralId': str(self.funcionario_zafral_id) if self.funcionario_zafral_id else None,
            'regimenLaboralId': str(self.regimen_laboral_id),
            'tipo': self.regimen_laboral.nombre if self.regimen_laboral else None,
            'fechaInicio': self.fecha_inicio.isoformat(),
            'fechaFin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'estado': self.estado,
            'sueldoNominal': float(self.sueldo_nominal) if self.sueldo_nominal is not None else None,
            'observaciones': self.observaciones,
            'tienePdf': bool(self.documento_key),
        }


class Asistencia(db.Model):
    __tablename__ = 'hr_asistencias'

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('hr_funcionarios.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='Presente')
    observaciones = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'funcionarioId': str(self.funcionario_id),
            'fecha': self.fecha.isoformat(),
            'estado': self.estado,
            'observaciones': self.observaciones,
        }


# ---------------------------------------------------------------------------
# Funcionarios Zafrales
# ---------------------------------------------------------------------------

class Tarea(db.Model):
    __tablename__ = 'hr_tareas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    funcionarios_zafrales = db.relationship('FuncionarioZafral', backref='tarea', lazy='dynamic')

    def to_dict(self):
        return {
            'id': str(self.id),
            'nombre': self.nombre,
        }


class FuncionarioZafral(db.Model):
    __tablename__ = 'hr_funcionarios_zafrales'

    id = db.Column(db.Integer, primary_key=True)
    ci = db.Column(db.String(30), unique=True, nullable=False)
    nombres = db.Column(db.String(150), nullable=False)
    apellidos = db.Column(db.String(150), nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    pais_nacimiento = db.Column(db.String(100), nullable=True)
    departamento_nacimiento = db.Column(db.String(100), nullable=True)
    estado_civil = db.Column(db.String(30), nullable=True)

    dependencia_id = db.Column(db.Integer, db.ForeignKey('hr_dependencias.id'), nullable=False)
    tarea_id = db.Column(db.Integer, db.ForeignKey('hr_tareas.id'), nullable=False)

    tipo_zafral = db.Column(db.String(50), nullable=False, default='Zafral Municipal')
    fecha_ingreso = db.Column(db.Date, nullable=False)
    regimen_laboral = db.Column(db.String(30), nullable=False, default='Full Time')
    estado = db.Column(db.String(30), nullable=False, default='Activo')
    motivo_baja = db.Column(db.String(255), nullable=True)
    inasistencias = db.Column(db.Integer, default=0)

    telefono = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    otro_contacto = db.Column(db.String(150), nullable=True)
    calle = db.Column(db.String(200), nullable=True)
    entre_calles = db.Column(db.String(200), nullable=True)
    zona = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    nivel_educativo = db.Column(db.String(100), nullable=True)
    otras_capacitaciones = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'ci': self.ci,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'genero': self.genero,
            'fechaNacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'paisNacimiento': self.pais_nacimiento,
            'departamentoNacimiento': self.departamento_nacimiento,
            'estadoCivil': self.estado_civil,
            'dependenciaId': str(self.dependencia_id),
            'tareaId': str(self.tarea_id),
            'tipoZafral': self.tipo_zafral,
            'fechaIngreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            'regimenLaboral': self.regimen_laboral,
            'estado': self.estado,
            'motivoBaja': self.motivo_baja,
            'inasistencias': self.inasistencias,
            'telefono': self.telefono,
            'email': self.email,
            'otroContacto': self.otro_contacto,
            'calle': self.calle,
            'entreCalles': self.entre_calles,
            'zona': self.zona,
            'observaciones': self.observaciones,
            'nivelEducativo': self.nivel_educativo,
            'otrasCapacitaciones': self.otras_capacitaciones,
        }


# ---------------------------------------------------------------------------
# Catálogos HR (tablas configurables desde el admin)
# ---------------------------------------------------------------------------

class RegimenLaboral(db.Model):
    __tablename__ = 'hr_regimenes_laborales'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class TipoZafralCat(db.Model):
    __tablename__ = 'hr_tipos_zafral'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class GeneroCat(db.Model):
    __tablename__ = 'hr_generos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class EstadoCivilCat(db.Model):
    __tablename__ = 'hr_estados_civiles'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class NivelEducativoCat(db.Model):
    __tablename__ = 'hr_niveles_educativos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class EstadoFuncionarioCat(db.Model):
    __tablename__ = 'hr_estados_funcionario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


class EstadoZafralCat(db.Model):
    __tablename__ = 'hr_estados_zafral'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {'id': str(self.id), 'nombre': self.nombre}


# ---------------------------------------------------------------------------
# Uruguay Impulsa
# ---------------------------------------------------------------------------

class UruguayImpulsaFuncionario(db.Model):
    __tablename__ = 'hr_uruguay_impulsa_funcionarios'

    id = db.Column(db.Integer, primary_key=True)
    area_funcion = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    apellido = db.Column(db.String(150), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    pais = db.Column(db.String(100), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    genero = db.Column(db.String(20), nullable=True)
    estado_civil = db.Column(db.String(30), nullable=True)
    tiene_hijos = db.Column(db.Boolean, default=False, nullable=False)
    cantidad_hijos = db.Column(db.Integer, default=0, nullable=False)
    cedula_identidad = db.Column(db.String(30), nullable=False, unique=True)
    calle = db.Column(db.String(200), nullable=True)
    entre_las_calles = db.Column(db.String(200), nullable=True)
    zona = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(30), nullable=True)
    mail = db.Column(db.String(150), nullable=True)
    primaria_estado = db.Column(db.String(20), nullable=True)
    ciclo_basico_estado = db.Column(db.String(20), nullable=True)
    bachillerato_estado = db.Column(db.String(20), nullable=True)
    terciario_estado = db.Column(db.String(20), nullable=True)
    capacitaciones = db.Column(db.Text, nullable=True)
    trabajos_anteriores = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        trabajos = []
        if self.trabajos_anteriores:
            try:
                import json
                trabajos = json.loads(self.trabajos_anteriores)
                if not isinstance(trabajos, list):
                    trabajos = []
            except Exception:
                trabajos = []

        return {
            'id': str(self.id),
            'areaFuncion': self.area_funcion,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'fechaNacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'pais': self.pais,
            'departamento': self.departamento,
            'genero': self.genero,
            'estadoCivil': self.estado_civil,
            'tieneHijos': self.tiene_hijos,
            'cantidadHijos': self.cantidad_hijos,
            'cedulaIdentidad': self.cedula_identidad,
            'calle': self.calle,
            'entreLasCalles': self.entre_las_calles,
            'zona': self.zona,
            'telefono': self.telefono,
            'mail': self.mail,
            'primariaEstado': self.primaria_estado,
            'cicloBasicoEstado': self.ciclo_basico_estado,
            'bachilleratoEstado': self.bachillerato_estado,
            'terciarioEstado': self.terciario_estado,
            'capacitaciones': self.capacitaciones,
            'trabajosAnteriores': trabajos,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }
