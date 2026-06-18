"""Seed idempotente de catálogos base de RRHH.

Comandos expuestos:
    - seed-data: carga áreas/dependencias, tareas zafrales y cargos.
"""

import click
from flask.cli import with_appcontext
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.hr import Cargo, Dependencia, NivelEducativoCat, Tarea


# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------

DEPENDENCIAS = [
    "Área Camping y Balnearios",
    "Área de Deportes",
    "Área de Familia, Genero y Generaciones.",
    "Área de Juventud",
    "Área de Parques y Paseos Públicos",
    "Área de Salud y Seguridad Ocupacional",
    "Área de Turismo",
    "CECOED",
    "Convivencia Departamental",
    "Coordinación",
    "Dirección de Desarrollo Económico, Productivo y Agropecuario.",
    "Dirección de Medio Ambiente",
    "Dirección de Prensa",
    "Dirección de Turismo",
    "Dirección General de Cultura",
    "Dirección General de Gestión Humana y Recursos Materiales",
    "Dirección General de Hacienda",
    "Dirección General de Salud y Bromatología",
    "Dirección General de Servicios Sociales",
    "Dirección General de Servicios Técnicos",
    "Dirección General de Tránsito, Seguridad y Convivencia Departamental.",
    "Dirección General de Urbanismo y Ordenamiento Territorial",
    "Dirección General de Vialidad y Obras",
    "Dirección General Jurídico Notarial",
    "Municipio de Solis de Mataojo",
    "Municipio José Batlle y Ordoñez",
    "Municipio José Pedro Varela",
    "Municipio Mariscala",
    "Municipio Pirarajá",
    "Municipio Zapicán",
]

TAREAS_ZAFRALES = [
    "Administrativo",
    "Albañil",
    "Chofer",
    "Cocinero",
    "Poda",
]

NIVELES_EDUCATIVOS = [
    ("Primaria Incompleta", 1),
    ("Primaria Completa", 2),
    ("Secundaria Incompleta", 3),
    ("Secundaria Completa", 4),
    ("Técnica No Universitaria Incompleta", 5),
    ("Técnica No Universitaria Completa", 6),
    ("Técnica Universitaria Incompleta", 7),
    ("Técnica Universitaria Completa", 8),
    ("Terciaria Incompleta", 9),
    ("Terciaria Completa", 10),
]

CARGOS = [
    "A03 - ODONTOLOGO",
    "A04 - QUIMICO",
    "A05 - MED. VETERINARIO JEFE",
    "A06 - MEDICO ASESOR",
    "A09 - ARQUITECTO ASESOR",
    "A10 - CONTADOR ASESOR",
    "A11 - INGENIERO ASESOR",
    "A12 - ABOGADO ASESOR",
    "A13 - ESCRIBANO (PRE)",
    "A13 C - ESCRIBANO CONTRATADO",
    "A15 - INGENIERO AGRIMENSOR",
    "A18 - PSICÓLOGO",
    "A20 - NUTRICIONISTA",
    "A21 - LICENCIADO EN TRABAJO SOCIAL",
    "A22 - SOCIOLOGO",
    "B02 - ANALISTA DE SISTEMAS",
    "B03 - TÉCNICO PREVENCIONISTA",
    "C02 - JEFE DE DIRECCION",
    "C03 - JEFE JTA.LOCAL MUNIC Y DEPTO",
    "C06 - JEFE DE SECCION",
    "C07 - JEFE DE SECTOR",
    "C08 - ADMINISTRATIVO I",
    "C09 - ADMINISTRATIVO II",
    "C10 - ADMINISTRATIVO III",
    "D01 - ESPECIALISTA I",
    "D02 - ESPECIALISTA II",
    "D03 - ESPECIALISTA III",
    "D04 - ESP. EN GESTIÓN AMBIENTAL",
    "E01 - MAQUINISTA I",
    "E02 - MAQUINISTA II",
    "E04 - CAPATAZ GENERAL",
    "E05 - CAPATAZ I",
    "E06 - CAPATAZ II",
    "E07 - OFICIAL I",
    "E08 - OFICIAL II",
    "E09 - MEDIO OFICIAL",
    "E10 - PEON PRACTICO",
    "E11 - PEON",
    "E13 - MAQUINISTA FINALISTA",
    "E14 - CHOFER ESPECIALIZADO 30HS.",
    "E15 - CHOFER 1era. 30 HS.",
    "E16 - CHOFER 2da. 30 HS.",
    "E17 - CAPATAZ GRAL. ELECTROTECNIA",
    "E18 - CAPATAZ 1RA. ELECTROTECNIA",
    "E19 - ELECTRICISTA 1RA.",
    "E20 - ELECTRICISTA 2DA.",
    "E24 - CHOFER ESPECIALIZADO 40 HS.",
    "E25 - CHOFER 1RA. 40 HS",
    "E26 - CHOFER 2DA. 40 HS.",
    "E27 - CAPATAZ GRAL (TALLERES)",
    "E28 - CAPATAZ 1RA. (TALLERES)",
    "E29 - OFICIAL I (TALLERES)",
    "E30 - OFICIAL II (TALLERES)",
    "F01 - JEFE DE SECCION",
    "F02 - AUXILIAR II - 6 HORAS",
    "F03 - AUXILIAR III - 6 HORAS",
    "F04 - AUXILIAR I - 6 HORAS",
    "H01 - MUSICOS",
    "H02 - DIRECTOR DE BANDA",
    "J03 - HORAS DOCENTES CULTURA",
    "J04 - PROFESOR DE PISCINA",
    "J05 - COORDINADOR PEDAGÓGICO",
    "J06 - MAESTRO DE ED. INICIAL",
    "J07 - EDUCADOR PREESCOLAR",
    "J08 - PROF. ED. FÍSICA POR HORAS",
    "J09 - HORA DOCENTE TECNICO",
    "JSOL - JORNALES SOLIDARIOS",
    "P01 - INTENDENTE MUNICIPAL",
    "P02 - ALCALDE JOSE PEDRO VARELA",
    "P03 - ALCALDE SOLIS",
    "P04 - ALCALDE BATLLE Y ORDOÑEZ",
    "P05 - ALCALDE MARISCALA",
    "P06 - ALCALDE PIRARAJA",
    "P07 - ALCALDE ZAPICAN",
    "Q01 - SECRETARIO GENERAL",
    "Q02 - DIR. GRAL. DE VIALIDAD Y OBRAS",
    "Q03 - DIRECTOR GENERAL DE HACIENDA",
    "Q04 - DIRECTOR GRAL. DE HIGIENE",
    "Q05 - DIR.GRAL. JURIDICO NOTARIAL",
    "Q06 - DIRECTOR GRAL. SERV. SOCIALES",
    "Q07 - DIRECTOR GRAL. SERV.TECNICOS",
    "Q08 - DIRECTOR GRAL. DEPTO CULTURA",
    "Q09 - DIR.GRAL.DE URB.Y ORD.TERRIT.",
    "Q10 - DIRECTOR GRAL. DE TRÁNSITO",
    "Q11 - DIRECTOR DE TURISMO",
    "Q12 - ENCARGADO DE DEPORTE",
    "Q13 - ENCARGADO DE JUVENTUD",
    "Q14 - DIR. DE ÁREA FAMILIA Y MUJER",
    "Q15 - ENC.DE CAMPINGS Y BALNEARIOS",
    "Q16 - DIRECTOR DE DES. AGROPECUARIO",
    "Q17 - DIR.DE PROMOCION Y DESARROLLO",
    "Q19 - COORDINADOR DE JUNTAS LOCALES",
    "Q20 - DIRECTOR DE MEDIO AMBIENTE",
    "Q21 - DIRECTOR DE PRENSA",
    "Q22 - ENC. DE PARQUES Y P.PUBLICOS",
    "Q23 - ENC. DE EDIFICIOS COMUNALES",
    "Q24 - DIR. DE PREVENCION Y SEGURIDAD",
    "Q25 - ENCARGADO CECOED",
    "Q26 - ENCARGADO DE DESCENTRALIZACION",
    "R02 - PROGRAMADOR",
    "R06 - INSPECTOR GENERAL",
    "R07 - INSPECTOR GENERAL 8 HS",
    "R08 - INSPECTOR I 6 HS.",
    "R09 - INSPECTOR II 6 HS.",
    "R10 - TECNICO LABORATORISTA",
    "R17 - INSPECTOR I 8 HS.",
    "R18 - INSPECTOR II 8 HS.",
    "R20 - BECARIOS",
    "R21 - TRABAJO JOVEN",
    "R22 - ENFERMERA",
    "X01 - PARTICULARES",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_cargo_line(linea: str):
    """Separa código y nombre usando el primer ' - '.

    Si no hay separador, devuelve código None y la línea completa como nombre.
    """
    if " - " in linea:
        codigo, nombre = linea.split(" - ", 1)
        return codigo.strip(), nombre.strip()
    return None, linea.strip()


# ---------------------------------------------------------------------------
# Seed principal
# ---------------------------------------------------------------------------

@click.command('seed-data')
@with_appcontext
def seed_data():
    """Carga o actualiza catálogos base: áreas/dependencias, tareas zafrales y cargos."""

    stats = {
        'dependencias': {'creadas': 0, 'existentes': 0},
        'tareas': {'creadas': 0, 'existentes': 0},
        'niveles_educativos': {'creadas': 0, 'existentes': 0},
        'cargos': {'creadas': 0, 'existentes': 0},
    }

    try:
        # ---------------- Áreas / Dependencias ----------------
        for nombre in DEPENDENCIAS:
            nombre = nombre.strip()
            if not nombre:
                continue
            existente = Dependencia.query.filter_by(nombre=nombre).first()
            if existente:
                stats['dependencias']['existentes'] += 1
            else:
                db.session.add(Dependencia(nombre=nombre))
                stats['dependencias']['creadas'] += 1

        # ---------------- Tareas zafrales ----------------
        for nombre in TAREAS_ZAFRALES:
            nombre = nombre.strip()
            if not nombre:
                continue
            existente = Tarea.query.filter_by(nombre=nombre).first()
            if existente:
                stats['tareas']['existentes'] += 1
            else:
                db.session.add(Tarea(nombre=nombre))
                stats['tareas']['creadas'] += 1

        # ---------------- Niveles educativos ----------------
        for item in NIVELES_EDUCATIVOS:
            if isinstance(item, tuple):
                nombre, orden = item
            else:
                nombre, orden = item, None
            nombre = nombre.strip()
            if not nombre:
                continue
            existente = NivelEducativoCat.query.filter_by(nombre=nombre).first()
            if existente:
                if orden is not None:
                    existente.orden = orden
                stats['niveles_educativos']['existentes'] += 1
            else:
                db.session.add(NivelEducativoCat(nombre=nombre, orden=orden))
                stats['niveles_educativos']['creadas'] += 1

        # ---------------- Cargos ----------------
        cargo_has_codigo = 'codigo' in Cargo.__table__.columns
        for linea in CARGOS:
            linea = linea.strip()
            if not linea:
                continue
            codigo, nombre = _split_cargo_line(linea)

            if cargo_has_codigo and codigo:
                existente = Cargo.query.filter_by(codigo=codigo).first()
                if existente:
                    stats['cargos']['existentes'] += 1
                else:
                    db.session.add(Cargo(codigo=codigo, nombre=nombre))
                    stats['cargos']['creadas'] += 1
            else:
                existente = Cargo.query.filter_by(nombre=linea).first()
                if existente:
                    stats['cargos']['existentes'] += 1
                else:
                    db.session.add(Cargo(nombre=linea))
                    stats['cargos']['creadas'] += 1

        db.session.commit()

        dep_total = stats['dependencias']['creadas'] + stats['dependencias']['existentes']
        tarea_total = stats['tareas']['creadas'] + stats['tareas']['existentes']
        nivel_total = stats['niveles_educativos']['creadas'] + stats['niveles_educativos']['existentes']
        cargo_total = stats['cargos']['creadas'] + stats['cargos']['existentes']

        click.echo("Seed ejecutado correctamente.")
        click.echo(f"Áreas/dependencias: {dep_total} procesadas ({stats['dependencias']['creadas']} creadas, {stats['dependencias']['existentes']} existentes).")
        click.echo(f"Tareas zafrales: {tarea_total} procesadas ({stats['tareas']['creadas']} creadas, {stats['tareas']['existentes']} existentes).")
        click.echo(f"Niveles educativos: {nivel_total} procesados ({stats['niveles_educativos']['creadas']} creados, {stats['niveles_educativos']['existentes']} existentes).")
        click.echo(f"Cargos: {cargo_total} procesados ({stats['cargos']['creadas']} creadas, {stats['cargos']['existentes']} existentes).")

    except SQLAlchemyError as exc:
        db.session.rollback()
        click.echo(f"ERROR: el seed falló y se hizo rollback. Detalle: {exc}", err=True)
        raise click.ClickException("No se pudieron cargar los catálogos base.")
