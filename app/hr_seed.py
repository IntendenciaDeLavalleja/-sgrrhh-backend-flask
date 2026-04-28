import click
from datetime import date
from flask.cli import with_appcontext
from app.extensions import db
from app.models.hr import (
    Asistencia, Cargo, Contrato, Dependencia, Funcionario, FuncionarioZafral,
    Tarea, TrabajoAnterior,
    EstadoCivilCat, EstadoEducacionCat, EstadoFuncionarioCat, EstadoZafralCat,
    GeneroCat, RegimenLaboral, TipoZafralCat,
)


@click.command('seed-hr-data')
@with_appcontext
def seed_hr_data():
    """Popula la base de datos HR con funcionarios regulares (presupuestados, contratados, etc.)."""

    # -------------------------------------------------- Dependencias
    deps_data = [
        ('dep-seed-1', 'Dirección de Vialidad'),
        ('dep-seed-2', 'Dirección de Higiene'),
        ('dep-seed-3', 'Dirección de Tránsito'),
        ('dep-seed-4', 'Área de Deportes'),
        ('dep-seed-5', 'Dirección de Turismo'),
        ('dep-seed-6', 'Dirección de Servicios Sociales'),
        ('dep-seed-7', 'Secretaría General'),
        ('dep-seed-8', 'Dirección de Obras'),
    ]
    dep_objs: dict[str, Dependencia] = {}
    for key, nombre in deps_data:
        existing = Dependencia.query.filter_by(nombre=nombre).first()
        if not existing:
            existing = Dependencia(nombre=nombre)
            db.session.add(existing)
            db.session.flush()
        dep_objs[key] = existing

    db.session.flush()
    click.echo(f'Dependencias: {len(dep_objs)}')

    # -------------------------------------------------- Cargos
    cargos_data = [
        ('car-seed-1', 'Administrativo',              'dep-seed-7'),
        ('car-seed-2', 'Auxiliar de limpieza',        'dep-seed-2'),
        ('car-seed-3', 'Chofer',                      'dep-seed-3'),
        ('car-seed-4', 'Conductor de maquinaria',     'dep-seed-1'),
        ('car-seed-5', 'Asistente de piscina',        'dep-seed-4'),
        ('car-seed-6', 'Técnico en tránsito',         'dep-seed-3'),
        ('car-seed-7', 'Cocinero',                    'dep-seed-6'),
        ('car-seed-8', 'Inspector de obras',          'dep-seed-8'),
        ('car-seed-9', 'Coordinador social',          'dep-seed-6'),
        ('car-seed-10', 'Encargado de mantenimiento', 'dep-seed-1'),
    ]
    cargo_objs: dict[str, Cargo] = {}
    for key, nombre, dep_key in cargos_data:
        dep = dep_objs[dep_key]
        existing = Cargo.query.filter_by(nombre=nombre, dependencia_id=dep.id).first()
        if not existing:
            existing = Cargo(nombre=nombre, dependencia_id=dep.id)
            db.session.add(existing)
            db.session.flush()
        cargo_objs[key] = existing

    db.session.flush()
    click.echo(f'Cargos: {len(cargo_objs)}')

    # -------------------------------------------------- Funcionarios regulares
    # Estados vÃ¡lidos: Presupuestado, Contratado, Baja, Licencia
    funcionarios_seed = [
        dict(
            ci='4567890-1',
            nombres='Lucía',
            apellidos='Fernández',
            genero='Femenino',
            fecha_nacimiento=date(1985, 4, 11),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Casado',
            dep_key='dep-seed-2',
            cargo_key='car-seed-2',
            fecha_ingreso=date(2015, 3, 1),
            regimen_laboral='30 horas',
            estado='Presupuestado',
            inasistencias=2,
            telefono='098123456',
            email='lucia.fernandez@intendencia.gub.uy',
            calle='18 de Julio 234',
            entre_calles='Sarandí y Treinta y Tres',
            zona='Centro',
            observaciones='Funcionaria de carrera. Excelente desempeño.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='No aplica',
            trabajos=[
                dict(empresa='Cooperativa Limpieza Sur', periodo='2010-2015', seccion='Mantenimiento', cargo='Auxiliar'),
            ],
        ),
        dict(
            ci='3987654-2',
            nombres='Martín',
            apellidos='Silva',
            genero='Masculino',
            fecha_nacimiento=date(1980, 9, 3),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-1',
            cargo_key='car-seed-4',
            fecha_ingreso=date(2018, 8, 15),
            regimen_laboral='Full Time',
            estado='Presupuestado',
            inasistencias=0,
            telefono='099456123',
            email='martin.silva@intendencia.gub.uy',
            observaciones='Maneja retroexcavadora y motoniveladora. Licencia categoría D.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='No aplica',
            trabajos=[],
        ),
        dict(
            ci='5123456-3',
            nombres='Paola',
            apellidos='Núñez',
            genero='Femenino',
            fecha_nacimiento=date(1990, 12, 20),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Montevideo',
            estado_civil='Concubinato',
            dep_key='dep-seed-7',
            cargo_key='car-seed-1',
            fecha_ingreso=date(2020, 1, 10),
            regimen_laboral='Full Time',
            estado='Contratado',
            inasistencias=1,
            telefono='094222111',
            email='paola.nunez@intendencia.gub.uy',
            observaciones='Contrato renovado anualmente. Manejo de expedientes.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
            trabajos=[
                dict(empresa='Ministerio de Educación', periodo='2016-2019', seccion='Mesa de Entrada', cargo='Administrativo'),
            ],
        ),
        dict(
            ci='2890012-7',
            nombres='Gonzalo',
            apellidos='Pérez',
            genero='Masculino',
            fecha_nacimiento=date(1975, 3, 5),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Divorciado',
            dep_key='dep-seed-3',
            cargo_key='car-seed-3',
            fecha_ingreso=date(2010, 2, 1),
            regimen_laboral='Full Time',
            estado='Presupuestado',
            inasistencias=0,
            telefono='092777444',
            email='gonzalo.perez@intendencia.gub.uy',
            observaciones='Chofer de flota liviana. Antigüedad de 15 años.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='No aplica',
            educacion_terciaria='No aplica',
            trabajos=[],
        ),
        dict(
            ci='4788123-9',
            nombres='Andrea',
            apellidos='Sosa',
            genero='Femenino',
            fecha_nacimiento=date(1988, 7, 19),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Canelones',
            estado_civil='Soltero',
            dep_key='dep-seed-6',
            cargo_key='car-seed-9',
            fecha_ingreso=date(2019, 11, 3),
            regimen_laboral='30 horas',
            estado='Baja',
            motivo_baja='Renuncia voluntaria.',
            inasistencias=0,
            telefono='095700333',
            email='andrea.sosa@intendencia.gub.uy',
            observaciones='Coordinaba programas de asistencia social.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Completa',
            trabajos=[],
        ),
        dict(
            ci='6234567-4',
            nombres='Roberto',
            apellidos='Castro',
            genero='Masculino',
            fecha_nacimiento=date(1983, 5, 22),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Casado',
            dep_key='dep-seed-8',
            cargo_key='car-seed-8',
            fecha_ingreso=date(2016, 11, 15),
            regimen_laboral='Full Time',
            estado='Presupuestado',
            inasistencias=3,
            telefono='093100200',
            email='roberto.castro@intendencia.gub.uy',
            observaciones='Inspector de obras civiles. Habilitado maestro de obras.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Completa',
            trabajos=[
                dict(empresa='Constructora del Este', periodo='2008-2016', seccion='Supervisión', cargo='Capataz'),
            ],
        ),
        dict(
            ci='7345678-5',
            nombres='Carolina',
            apellidos='Méndez',
            genero='Femenino',
            fecha_nacimiento=date(1992, 8, 14),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-4',
            cargo_key='car-seed-5',
            fecha_ingreso=date(2022, 2, 1),
            regimen_laboral='20 horas',
            estado='Contratado',
            inasistencias=4,
            telefono='091555666',
            email='carolina.mendez@intendencia.gub.uy',
            observaciones='Contrato vigente. Responsable de actividades acuáticas.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
            trabajos=[],
        ),
        dict(
            ci='8901234-6',
            nombres='Fernando',
            apellidos='Acosta',
            genero='Masculino',
            fecha_nacimiento=date(1978, 11, 30),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Casado',
            dep_key='dep-seed-3',
            cargo_key='car-seed-6',
            fecha_ingreso=date(2008, 6, 1),
            regimen_laboral='Full Time',
            estado='Licencia',
            inasistencias=0,
            telefono='096321987',
            email='fernando.acosta@intendencia.gub.uy',
            calle='General Rivera 567',
            zona='Barrio Jardín',
            observaciones='Licencia médica por intervención quirúrgica. Reincorporación prevista en 60 días.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Completa',
            trabajos=[
                dict(empresa='Policía Caminera', periodo='2004-2008', seccion='Tránsito', cargo='Auxiliar'),
            ],
        ),
        dict(
            ci='9012345-8',
            nombres='Natalia',
            apellidos='Sánchez',
            genero='Femenino',
            fecha_nacimiento=date(1995, 2, 17),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-7',
            cargo_key='car-seed-1',
            fecha_ingreso=date(2023, 4, 1),
            regimen_laboral='Full Time',
            estado='Contratado',
            inasistencias=0,
            telefono='097890123',
            email='natalia.sanchez@intendencia.gub.uy',
            calle='Treinta y Tres 890',
            zona='Centro',
            observaciones='Ingreso reciente. Buena adaptación al equipo.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Completa',
            trabajos=[],
        ),
        dict(
            ci='1234567-0',
            nombres='Jorge',
            apellidos='Ramírez',
            genero='Masculino',
            fecha_nacimiento=date(1970, 6, 8),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Casado',
            dep_key='dep-seed-1',
            cargo_key='car-seed-10',
            fecha_ingreso=date(2000, 3, 15),
            regimen_laboral='Full Time',
            estado='Presupuestado',
            inasistencias=1,
            telefono='098765432',
            email='jorge.ramirez@intendencia.gub.uy',
            calle='Artigas 123',
            entre_calles='Colón y Florida',
            zona='Centro',
            observaciones='Funcionario de mayor antigüedad de la dirección. Supervisión de cuadrillas.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='No aplica',
            educacion_terciaria='No aplica',
            trabajos=[],
        ),
    ]

    fun_objs: list[Funcionario] = []
    for fd in funcionarios_seed:
        existing = Funcionario.query.filter_by(ci=fd['ci']).first()
        if existing:
            fun_objs.append(existing)
            continue

        fun = Funcionario(
            ci=fd['ci'],
            nombres=fd['nombres'],
            apellidos=fd['apellidos'],
            genero=fd['genero'],
            fecha_nacimiento=fd.get('fecha_nacimiento'),
            pais_nacimiento=fd.get('pais_nacimiento'),
            departamento_nacimiento=fd.get('departamento_nacimiento'),
            estado_civil=fd.get('estado_civil'),
            dependencia_id=dep_objs[fd['dep_key']].id,
            cargo_id=cargo_objs[fd['cargo_key']].id,
            fecha_ingreso=fd['fecha_ingreso'],
            regimen_laboral=fd['regimen_laboral'],
            estado=fd['estado'],
            motivo_baja=fd.get('motivo_baja'),
            inasistencias=fd.get('inasistencias', 0),
            telefono=fd.get('telefono'),
            email=fd.get('email'),
            calle=fd.get('calle'),
            entre_calles=fd.get('entre_calles'),
            zona=fd.get('zona'),
            observaciones=fd.get('observaciones'),
            educacion_primaria=fd.get('educacion_primaria'),
            educacion_secundaria=fd.get('educacion_secundaria'),
            educacion_bachillerato=fd.get('educacion_bachillerato'),
            educacion_terciaria=fd.get('educacion_terciaria'),
        )
        db.session.add(fun)
        db.session.flush()

        for ta in fd.get('trabajos', []):
            db.session.add(TrabajoAnterior(
                funcionario_id=fun.id,
                empresa=ta['empresa'],
                periodo=ta.get('periodo'),
                seccion=ta.get('seccion'),
                cargo=ta.get('cargo'),
            ))

        fun_objs.append(fun)

    db.session.flush()
    click.echo(f'Funcionarios: {len(fun_objs)}')

    # -------------------------------------------------- Contratos
    contratos_seed = [
        dict(fun_idx=0, tipo='Permanente',   fecha_inicio=date(2015, 3, 1),  fecha_fin=date(2030, 12, 31), estado='Vigente',     sueldo=55000.0, obs='Contrato por tiempo indeterminado.'),
        dict(fun_idx=1, tipo='Permanente',   fecha_inicio=date(2018, 8, 15), fecha_fin=date(2030, 12, 31), estado='Vigente',     sueldo=62000.0),
        dict(fun_idx=2, tipo='Temporal',     fecha_inicio=date(2024, 1, 10), fecha_fin=date(2026, 1, 10), estado='Por vencer',  sueldo=48500.0, obs='Renovable previa evaluación de desempeño.'),
        dict(fun_idx=3, tipo='Permanente',   fecha_inicio=date(2010, 2, 1),  fecha_fin=date(2030, 12, 31), estado='Vigente',     sueldo=58000.0),
        dict(fun_idx=6, tipo='Temporal',     fecha_inicio=date(2022, 2, 1),  fecha_fin=date(2026, 7, 1),  estado='Por vencer',  sueldo=42000.0),
        dict(fun_idx=5, tipo='Permanente',   fecha_inicio=date(2016, 11, 15), fecha_fin=date(2030, 12, 31), estado='Vigente',    sueldo=64000.0),
        dict(fun_idx=7, tipo='Suplencia',    fecha_inicio=date(2025, 1, 1),  fecha_fin=date(2025, 7, 31), estado='Vencido',     sueldo=45000.0, obs='Suplencia durante licencia médica del titular.'),
        dict(fun_idx=8, tipo='Temporal',     fecha_inicio=date(2023, 4, 1),  fecha_fin=date(2027, 4, 1),  estado='Vigente',     sueldo=51000.0),
        dict(fun_idx=9, tipo='Permanente',   fecha_inicio=date(2000, 3, 15), fecha_fin=date(2030, 12, 31), estado='Vigente',     sueldo=70000.0, obs='Funcionario de carrera con 25 años de antigüedad.'),
    ]
    contratos_count = 0
    for cd in contratos_seed:
        fun = fun_objs[cd['fun_idx']]
        exists = Contrato.query.filter_by(funcionario_id=fun.id, tipo=cd['tipo'], fecha_inicio=cd['fecha_inicio']).first()
        if not exists:
            c = Contrato(
                funcionario_id=fun.id,
                tipo=cd['tipo'],
                fecha_inicio=cd['fecha_inicio'],
                fecha_fin=cd['fecha_fin'],
                estado=cd['estado'],
                sueldo_nominal=cd.get('sueldo'),
                observaciones=cd.get('obs'),
            )
            db.session.add(c)
            contratos_count += 1

    db.session.flush()
    click.echo(f'Contratos nuevos: {contratos_count}')

    # -------------------------------------------------- Asistencias (Ãºltimos 10 dÃ­as laborables)
    from datetime import timedelta
    today = date.today()
    asistencias_count = 0
    estados_rotacion = ['Presente', 'Presente', 'Presente', 'Falta', 'Licencia']

    for fun_idx, fun in enumerate(fun_objs[:7]):  # primeros 7 activos
        dias_trabajados = 0
        check_day = today - timedelta(days=1)
        while dias_trabajados < 10:
            if check_day.weekday() < 5:  # lunesâ€“viernes
                exists = Asistencia.query.filter_by(funcionario_id=fun.id, fecha=check_day).first()
                if not exists:
                    estado = estados_rotacion[(fun_idx + dias_trabajados) % len(estados_rotacion)]
                    db.session.add(Asistencia(
                        funcionario_id=fun.id,
                        fecha=check_day,
                        estado=estado,
                    ))
                    asistencias_count += 1
                dias_trabajados += 1
            check_day -= timedelta(days=1)

    db.session.commit()
    click.echo(f'Asistencias nuevas: {asistencias_count}')
    click.echo('[OK] Seed HR completado.')


@click.command('seed-zafrales-data')
@with_appcontext
def seed_zafrales_data():
    """Popula la base de datos con funcionarios zafrales (tabla separada hr_funcionarios_zafrales)."""

    # -------------------------------------------------- Dependencias (reusar o crear)
    dep_objs: dict[str, Dependencia] = {}
    deps_data = [
        ('dep-seed-1', 'Dirección de Vialidad'),
        ('dep-seed-2', 'Dirección de Higiene'),
        ('dep-seed-3', 'Dirección de Tránsito'),
        ('dep-seed-4', 'Área de Deportes'),
        ('dep-seed-5', 'Dirección de Turismo'),
        ('dep-seed-6', 'Dirección de Servicios Sociales'),
        ('dep-seed-7', 'Secretaría General'),
        ('dep-seed-8', 'Dirección de Obras'),
    ]
    for key, nombre in deps_data:
        existing = Dependencia.query.filter_by(nombre=nombre).first()
        if not existing:
            existing = Dependencia(nombre=nombre)
            db.session.add(existing)
            db.session.flush()
        dep_objs[key] = existing

    db.session.flush()

    # -------------------------------------------------- Tareas (propias del circuito zafral)
    tareas_data = [
        ('tar-seed-1',  'Corte de pasto',                   'dep-seed-1'),
        ('tar-seed-2',  'Limpieza de calles',               'dep-seed-2'),
        ('tar-seed-3',  'Apoyo en cocina comunitaria',      'dep-seed-6'),
        ('tar-seed-4',  'Mantenimiento de espacios públicos','dep-seed-1'),
        ('tar-seed-5',  'Poda de árboles',                  'dep-seed-1'),
        ('tar-seed-6',  'Pintura de cordones',              'dep-seed-2'),
        ('tar-seed-7',  'Limpieza de playas',               'dep-seed-5'),
        ('tar-seed-8',  'Apoyo en eventos deportivos',      'dep-seed-4'),
        ('tar-seed-9',  'Atención al público - turismo',    'dep-seed-5'),
        ('tar-seed-10', 'Barrido de plazas y paseos',       'dep-seed-2'),
        ('tar-seed-11', 'Pintura de edificios municipales', 'dep-seed-8'),
        ('tar-seed-12', 'Apoyo administrativo',             'dep-seed-7'),
    ]
    tarea_objs: dict[str, Tarea] = {}
    for key, nombre, dep_key in tareas_data:
        dep = dep_objs[dep_key]
        existing = Tarea.query.filter_by(nombre=nombre, dependencia_id=dep.id).first()
        if not existing:
            existing = Tarea(nombre=nombre, dependencia_id=dep.id)
            db.session.add(existing)
            db.session.flush()
        tarea_objs[key] = existing

    db.session.flush()
    click.echo(f'Tareas: {len(tarea_objs)}')

    # -------------------------------------------------- Funcionarios Zafrales
    # Estados vÃ¡lidos: Activo, Baja
    zafrales_seed = [
        dict(
            ci='8123456-1',
            nombres='Sebastián',
            apellidos='Rodríguez',
            genero='Masculino',
            fecha_nacimiento=date(2000, 3, 14),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-2',
            tarea_key='tar-seed-2',
            tipo_zafral='Uruguay Impulsa',
            fecha_ingreso=date(2025, 1, 6),
            regimen_laboral='Jornalero',
            estado='Activo',
            inasistencias=1,
            telefono='098001122',
            email='sebastian.rodriguez@correo.com',
            calle='Treinta y Tres 456',
            zona='Centro',
            observaciones='Participante del programa Uruguay Impulsa.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Incompleta',
            educacion_terciaria='No aplica',
        ),
        dict(
            ci='9234567-2',
            nombres='Valentina',
            apellidos='Gómez',
            genero='Femenino',
            fecha_nacimiento=date(2003, 7, 22),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-4',
            tarea_key='tar-seed-8',
            tipo_zafral='Yo estudio y trabajo',
            fecha_ingreso=date(2025, 2, 3),
            regimen_laboral='20 horas',
            estado='Activo',
            inasistencias=0,
            telefono='097223344',
            email='valentina.gomez@correo.com',
            zona='Barrio Norte',
            observaciones='Estudiante de educación física. Combina estudio con trabajo en temporada.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
        ),
        dict(
            ci='7890123-3',
            nombres='Diego',
            apellidos='Martínez',
            genero='Masculino',
            fecha_nacimiento=date(2001, 11, 5),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Treinta y Tres',
            estado_civil='Soltero',
            dep_key='dep-seed-1',
            tarea_key='tar-seed-1',
            tipo_zafral='Pasantía',
            fecha_ingreso=date(2025, 3, 1),
            regimen_laboral='20 horas',
            estado='Activo',
            inasistencias=0,
            telefono='096334455',
            email='diego.martinez@correo.com',
            zona='Barrio Sur',
            observaciones='Pasante de técnico en mantenimiento urbano. Convenio UTU.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
        ),
        dict(
            ci='6789012-4',
            nombres='Florencia',
            apellidos='López',
            genero='Femenino',
            fecha_nacimiento=date(1995, 5, 18),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Casado',
            dep_key='dep-seed-6',
            tarea_key='tar-seed-3',
            tipo_zafral='Zafral Municipal',
            fecha_ingreso=date(2024, 12, 2),
            regimen_laboral='30 horas',
            estado='Activo',
            inasistencias=2,
            telefono='095445566',
            email='florencia.lopez@correo.com',
            calle='Artigas 789',
            entre_calles='Rivera y Batlle',
            zona='Centro',
            observaciones='Apoyo en comedor comunitario de temporada estival.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='No aplica',
        ),
        dict(
            ci='5678901-5',
            nombres='Emilio',
            apellidos='Herrera',
            genero='Masculino',
            fecha_nacimiento=date(1998, 9, 30),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Maldonado',
            estado_civil='Soltero',
            dep_key='dep-seed-5',
            tarea_key='tar-seed-7',
            tipo_zafral='Zafral Municipal',
            fecha_ingreso=date(2025, 1, 13),
            regimen_laboral='Jornalero',
            estado='Activo',
            inasistencias=0,
            telefono='094556677',
            email='emilio.herrera@correo.com',
            zona='Costa',
            observaciones='Limpieza de playas en temporada estival. Zona Laguna de los Cisnes.',
            educacion_primaria='Completa',
            educacion_secundaria='Incompleta',
            educacion_bachillerato='No aplica',
            educacion_terciaria='No aplica',
        ),
        dict(
            ci='4567890-6',
            nombres='Camila',
            apellidos='Benítez',
            genero='Femenino',
            fecha_nacimiento=date(2002, 4, 8),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-1',
            tarea_key='tar-seed-4',
            tipo_zafral='Uruguay Impulsa',
            fecha_ingreso=date(2025, 2, 17),
            regimen_laboral='Jornalero',
            estado='Activo',
            inasistencias=1,
            telefono='093667788',
            email='camila.benitez@correo.com',
            zona='Barrio Obrero',
            observaciones='Tareas de mantenimiento en parques y plazas. Programa Uruguay Impulsa.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Incompleta',
            educacion_terciaria='No aplica',
        ),
        dict(
            ci='3456789-7',
            nombres='Lucas',
            apellidos='Ríos',
            genero='Masculino',
            fecha_nacimiento=date(1999, 12, 25),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Concubinato',
            dep_key='dep-seed-2',
            tarea_key='tar-seed-10',
            tipo_zafral='Yo estudio y trabajo',
            fecha_ingreso=date(2025, 1, 20),
            regimen_laboral='20 horas',
            estado='Baja',
            motivo_baja='Finalización de período de prueba.',
            inasistencias=4,
            telefono='092778899',
            email='lucas.rios@correo.com',
            zona='Villa del Carmen',
            observaciones='Barrido de plazas zona norte. Egresó por no superar período de prueba.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='No aplica',
        ),
        dict(
            ci='2345678-8',
            nombres='Micaela',
            apellidos='Torres',
            genero='Femenino',
            fecha_nacimiento=date(2004, 8, 19),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-5',
            tarea_key='tar-seed-9',
            tipo_zafral='Yo estudio y trabajo',
            fecha_ingreso=date(2025, 1, 6),
            regimen_laboral='20 horas',
            estado='Activo',
            inasistencias=0,
            telefono='091889900',
            email='micaela.torres@correo.com',
            zona='Centro',
            observaciones='Atención al turista en temporada. Manejo básico de inglés.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
        ),
        dict(
            ci='1234560-9',
            nombres='Rodrigo',
            apellidos='Delgado',
            genero='Masculino',
            fecha_nacimiento=date(2001, 5, 12),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-8',
            tarea_key='tar-seed-11',
            tipo_zafral='Pasantía',
            fecha_ingreso=date(2025, 2, 3),
            regimen_laboral='30 horas',
            estado='Activo',
            inasistencias=0,
            telefono='098112233',
            email='rodrigo.delgado@correo.com',
            zona='Barrio Industrial',
            observaciones='Pasante de construcción. Convenio con UTU Minas.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
        ),
        dict(
            ci='0987654-0',
            nombres='Agustina',
            apellidos='Quintero',
            genero='Femenino',
            fecha_nacimiento=date(2003, 1, 28),
            pais_nacimiento='Uruguay',
            departamento_nacimiento='Lavalleja',
            estado_civil='Soltero',
            dep_key='dep-seed-7',
            tarea_key='tar-seed-12',
            tipo_zafral='Uruguay Impulsa',
            fecha_ingreso=date(2025, 3, 10),
            regimen_laboral='20 horas',
            estado='Activo',
            inasistencias=0,
            telefono='097334455',
            email='agustina.quintero@correo.com',
            zona='Centro',
            observaciones='Apoyo administrativo en secretaría. Manejo de herramientas ofimáticas.',
            educacion_primaria='Completa',
            educacion_secundaria='Completa',
            educacion_bachillerato='Completa',
            educacion_terciaria='Incompleta',
        ),
    ]

    fz_objs: list[FuncionarioZafral] = []
    for fd in zafrales_seed:
        existing = FuncionarioZafral.query.filter_by(ci=fd['ci']).first()
        if existing:
            fz_objs.append(existing)
            continue

        fz = FuncionarioZafral(
            ci=fd['ci'],
            nombres=fd['nombres'],
            apellidos=fd['apellidos'],
            genero=fd['genero'],
            fecha_nacimiento=fd.get('fecha_nacimiento'),
            pais_nacimiento=fd.get('pais_nacimiento'),
            departamento_nacimiento=fd.get('departamento_nacimiento'),
            estado_civil=fd.get('estado_civil'),
            dependencia_id=dep_objs[fd['dep_key']].id,
            tarea_id=tarea_objs[fd['tarea_key']].id,
            tipo_zafral=fd['tipo_zafral'],
            fecha_ingreso=fd['fecha_ingreso'],
            regimen_laboral=fd['regimen_laboral'],
            estado=fd['estado'],
            motivo_baja=fd.get('motivo_baja'),
            inasistencias=fd.get('inasistencias', 0),
            telefono=fd.get('telefono'),
            email=fd.get('email'),
            calle=fd.get('calle'),
            entre_calles=fd.get('entre_calles'),
            zona=fd.get('zona'),
            observaciones=fd.get('observaciones'),
            educacion_primaria=fd.get('educacion_primaria'),
            educacion_secundaria=fd.get('educacion_secundaria'),
            educacion_bachillerato=fd.get('educacion_bachillerato'),
            educacion_terciaria=fd.get('educacion_terciaria'),
        )
        db.session.add(fz)
        fz_objs.append(fz)

    db.session.commit()
    click.echo(f'Funcionarios Zafrales: {len(fz_objs)}')
    click.echo('[OK] Seed Zafrales completado.')


@click.command('seed-catalog-data')
@with_appcontext
def seed_catalog_data():
    """Popula los catÃ¡logos HR (regÃ­menes, gÃ©neros, estados, etc.) con valores predeterminados."""

    def _seed(model, names):
        existing = {r.nombre for r in model.query.all()}
        count = 0
        for i, name in enumerate(names):
            if name not in existing:
                db.session.add(model(nombre=name, orden=i))
                count += 1
        db.session.flush()
        return count

    r = _seed(RegimenLaboral, ['Jornalero', '20 horas', '30 horas', 'Full Time', 'No aplica'])
    click.echo(f'Regímenes Laborales: {r} nuevos')

    t = _seed(TipoZafralCat, ['Uruguay Impulsa', 'Yo estudio y trabajo', 'Pasantía', 'Zafral Municipal'])
    click.echo(f'Tipos de Zafral: {t} nuevos')

    g = _seed(GeneroCat, ['Masculino', 'Femenino', 'Neutro'])
    click.echo(f'Géneros: {g} nuevos')

    ec = _seed(EstadoCivilCat, ['Soltero', 'Casado', 'Divorciado', 'Concubinato', 'Viudo', 'Separado', 'Otro'])
    click.echo(f'Estados Civiles: {ec} nuevos')

    ee = _seed(EstadoEducacionCat, ['Completa', 'Incompleta', 'No aplica'])
    click.echo(f'Estados Educación: {ee} nuevos')

    # Estados de Funcionario regular (NO incluye Zafral â€” esos van por FuncionarioZafral)
    ef = _seed(EstadoFuncionarioCat, ['Presupuestado', 'Contratado', 'Licencia', 'Baja'])
    click.echo(f'Estados Funcionario: {ef} nuevos')

    ez = _seed(EstadoZafralCat, ['Activo', 'Baja'])
    click.echo(f'Estados Zafral: {ez} nuevos')

    db.session.commit()
    click.echo('[OK] Seed Catalogos completado.')



