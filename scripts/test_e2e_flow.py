#!/usr/bin/env python3
"""End-to-end test script for Sentinel AcademIA with VARIED content.

Generates realistic, varied complaints across all categories.
Use this for simulations, demos, and load testing.

Usage:
    python3 scripts/test_e2e_flow.py [--count N] [--no-infra]
"""

from __future__ import annotations

import argparse
import random
import sys
import time
import uuid
from datetime import datetime, timedelta

import requests

API_BASE = "https://om3eiczjr9.execute-api.us-east-1.amazonaws.com/dev"
TENANT = "demo-utec"

# Names pool for variety in emails
NOMBRES = [
    "maria.lopez", "juan.perez", "ana.garcia", "carlos.rodriguez", "luis.torres",
    "sofia.mendez", "diego.hernandez", "valentina.cruz", "sebastian.diaz",
    "camila.vega", "matias.soto", "isabella.flores", "nicolas.castro", "valeria.ruiz",
    "sebastian.morales", "emilia.rojas", "tomas.silva", "renata.acosta", "agustin.medina",
    "constanza.ibarra", "maximiliano.duarte", "antonella.suarez", "joaquin.aguirre",
    "maria.fernanda.quiroz", "gabriel.salazar", "florencia.benitez", "lucas.arrieta",
]

APELLIDOS = [
    "Profesor de Calculo II", "Profesora de Literatura", "Profesor de Programacion",
    "Profesora de Quimica", "Profesor de Fisica", "Profesora de Estadistica",
    "Director de carrera", "Coordinador academico", "Jefe de departamento",
    "Asistente administrativo", "Personal de limpieza", "Seguridad del campus",
    "Cajero de cafeteria", "Bibliotecario", "Decano de facultad",
    "Companero de clase", "Tutor", "Compa\u00f1ero de laboratorio",
]

# CURSOS pool for ACADEMICA
CURSOS = [
    ("CS101", "Programacion I"),
    ("CS201", "Algoritmos y Estructuras de Datos"),
    ("MAT101", "Calculo I"),
    ("MAT201", "Calculo II"),
    ("FIS101", "Fisica I"),
    ("EST204", "Estadistica Aplicada"),
    ("QUI101", "Quimica General"),
    ("ING301", "Ingenieria de Software"),
    ("ADM201", "Administracion de Empresas"),
    ("ECO101", "Microeconomia"),
    ("LET101", "Literatura Hispanoamericana"),
    ("FIL101", "Filosofia"),
    ("HIS101", "Historia Universal"),
    ("PSI301", "Psicologia Organizacional"),
    ("DER101", "Derecho Constitucional"),
]

# Buildings / locations for INFRAESTRUCTURA
UBICACIONES_INFRA = [
    ("edificio A", "primer piso", "los banos de hombres"),
    ("edificio A", "segundo piso", "los servicios higienicos"),
    ("edificio A", "tercer piso", "los bebederos"),
    ("edificio B", "planta baja", "la cafeteria"),
    ("edificio B", "primer piso", "las aulas 101-105"),
    ("edificio B", "segundo piso", "los laboratorios de computo"),
    ("edificio C", "primer piso", "la biblioteca"),
    ("edificio C", "segundo piso", "las aulas de dibujo"),
    ("edificio C", "tercer piso", "los ascensores"),
    ("edificio D", "todos los pisos", "el sistema de aire acondicionado"),
    ("edificio D", "primer piso", "la entrada principal"),
    ("edificio D", "segundo piso", "las escaleras de emergencia"),
    ("edificio E", "planta baja", "el laboratorio de quimica"),
    ("edificio E", "primer piso", "la sala de profesores"),
    ("edificio E", "segundo piso", "los banos mixtos"),
    ("exteriores", "estacionamiento", "las luminarias"),
    ("exteriores", "patio central", "las mesas y bancas"),
    ("exteriores", "cancha deportiva", "las porterias y redes"),
]

PROBLEMAS_INFRA = [
    "estan en muy mal estado", "no funcionan correctamente", "no se les ha dado mantenimiento",
    "presentan fallas recurrentes", "no cumplen con normas basicas de higiene",
    "representan un riesgo para la salud", "impiden el normal desarrollo de las clases",
    "generan incomodidad a los estudiantes", "son un peligro para la seguridad",
]

# ACOSO templates with variety
TIPOS_ACOSO = [
    ("sexual", "El {actor} me ha estado acosando {tiempo}. {contexto}"),
    ("verbal", "El {actor} me hostiga verbalmente con {contexto}"),
    ("discriminacion", "He sufrido discriminacion por parte del {actor}. {contexto}"),
    ("ciberacoso", "Estoy recibiendo {contexto} del {actor} {tiempo}"),
    ("academico", "El {actor} me amenaza con {contexto} si no acepto sus condiciones"),
]

ACTORES_ACOSO = [
    "profesor de {curso}",
    "profesora del curso {curso}",
    "compa\u00f1ero de clase",
    "compa\u00f1era del grupo de laboratorio",
    "asistente administrativo",
    "supervisor de practicas",
]

CONTEXTOS_ACOSO = [
    "mensajes inapropiados, insinuaciones de contenido sexual y amenazas de bajarme la nota si no acepto sus propuestas",
    "comentarios racistas y humillaciones publicas delante de toda la clase",
    "insinuaciones no deseadas, manoseos en el aula y presion para encuentros privados",
    "fotografias intimas compartidas en grupos sin mi consentimiento",
    "burlas constantes por mi origen socioeconomico y amenazas con aislarme del grupo",
    "comentarios sexistas y misoginos repetidos en cada clase",
    "intimidacion academica, chantaje emocional y amenazas de dao academico",
    "compartir mis datos personales en redes sociales para acosarme",
]

TIEMPOS_ACOSO = ["hace 2 semanas", "desde hace 1 mes", "durante el ultimo semestre",
                  "por mas de 3 meses", "reiteradamente este ciclo"]


def random_email() -> str:
    """Generate a random @utec.edu.pe email."""
    nombre = random.choice(NOMBRES)
    suffix = random.randint(10, 99) if random.random() < 0.3 else ""
    return f"{nombre}{suffix}@utec.edu.pe"


def random_acoso() -> dict:
    """Generate a varied ACOSO complaint."""
    tipo, plantilla = random.choice(TIPOS_ACOSO)
    actor_template = random.choice(ACTORES_ACOSO)
    curso = random.choice(CURSOS)[0]
    actor = actor_template.format(curso=curso)
    contexto = random.choice(CONTEXTOS_ACOSO)
    tiempo = random.choice(TIEMPOS_ACOSO)
    descripcion = plantilla.format(actor=actor, tiempo=tiempo, contexto=contexto)
    titulo = f"Denuncia de acoso {tipo} por parte de {actor.split(' ')[0]}"
    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "reportante_email": random_email(),
    }


def random_academica() -> dict:
    """Generate a varied ACADEMICA complaint."""
    curso_codigo, curso_nombre = random.choice(CURSOS)
    problemas = [
        f"El profesor del curso {curso_codigo} ({curso_nombre}) no ha subido las notas del examen final hace 4 semanas",
        f"El metodo de evaluacion del curso {curso_codigo} no coincide con el silabo oficial",
        f"Las clases del curso {curso_codigo} se cancelan constantemente sin aviso previo",
        f"El material didactico del curso {curso_codigo} esta desactualizado y no cubre los temas del examen",
        f"El profesor del curso {curso_codigo} no responde correos ni dudas de los estudiantes",
        f"Hay errores graves en las calificaciones del curso {curso_codigo} que afectan a todo el grupo",
    ]
    detalles = [
        "Esto esta afectando mi promedio y mi postulacion a practicas profesionales",
        "Varios companeros hemos reclamado y no obtenemos respuesta",
        "El silabo dice claramente que la metodologia es X pero el profesor aplica Y",
        "Ya envie 3 correos sin obtener respuesta en 2 semanas",
        "El promedio del grupo bajo 2 puntos en relacion al semestre anterior",
    ]
    return {
        "titulo": f"Problema academico en curso {curso_codigo} - {curso_nombre}",
        "descripcion": f"{random.choice(problemas)}. {random.choice(detalles)}.",
        "reportante_email": random_email(),
        "cursoCodigo": curso_codigo,
    }


def random_administrativa() -> dict:
    """Generate a varied ADMINISTRATIVA complaint."""
    problemas = [
        ("Problema con matricula", "El sistema no me dejo inscribirme en 2 cursos que necesito para graduarme"),
        ("Error en emision de certificado", "Solicite mi certificado de estudios hace 3 semanas y no he recibido respuesta"),
        ("Cobro indebido", "Me cobraron un monto que no corresponde al servicio contratado"),
        ("Problema con convalidacion", "La convalidacion de mi curso de la universidad anterior lleva 2 meses sin resolverse"),
        ("Falta de respuesta de registro", "Llevo un mes intentando comunicarme con la oficina de registros academicos sin exito"),
    ]
    titulo, descripcion = random.choice(problemas)
    return {
        "titulo": titulo,
        "descripcion": f"{descripcion}. La oficina de registros no da respuesta y se acerca el cierre del semestre.",
        "reportante_email": random_email(),
    }


def random_salud() -> dict:
    """Generate a varied SALUD complaint."""
    situaciones = [
        ("Necesito apoyo psicologico urgente", "Estoy pasando por un momento muy dificil emocionalmente, con ataques de panico frecuentes y problemas para concentrarme en los estudios. Necesito hablar con un psicologo de bienestar lo antes posible."),
        ("Problemas de ansiedad academica", "La carga academica y las exigencias del semestre me han generado ansiedad cronica. Busco apoyo profesional del area de bienestar."),
        ("Aislamiento social en el campus", "Me siento completamente solo y aislado del grupo. No tengo amigos ni red de apoyo. Esto esta afectando mi rendimiento academico."),
        ("Estres post-traumatico", "Vivo con secuelas de una situacion traumatica y necesito apoyo psicologico especializado del servicio de bienestar."),
        ("Burnout academico severo", "Llevo semanas sin poder dormir bien, con agotamiento fisico y mental. Necesito ayuda profesional antes de colapsar."),
    ]
    titulo, descripcion = random.choice(situaciones)
    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "reportante_email": random_email(),
    }


def random_infraestructura(num_variants: int) -> list[dict]:
    """Generate N INFRAESTRUCTURA complaints about the same issue but varied."""
    edificio, piso, lugar = random.choice(UBICACIONES_INFRA)
    problema = random.choice(PROBLEMAS_INFRA)
    base_desc = (
        f"Los {lugar} del {edificio} ({piso}) {problema}. "
        f"Esto afecta a todos los estudiantes que usamos estas instalaciones diariamente."
    )
    extras = [
        "llevo semanas reclamando y no hay respuesta",
        "los profesores tambien se han quejado",
        "es un problema de salud publica",
        "no se puede estudiar ni comer tranquilo asi",
        "el senor de limpieza no aparece por aqui",
        "viene gente de afuera y da verguenza",
        "el semestre pasado estaba igual y nunca lo arreglaron",
        "ya hemos hecho colecta para contratar una limpieza temporal",
        "sera el fin de semestre y siguen igual",
        "necesitamos mantenimiento urgente",
    ]
    out = []
    random.shuffle(extras)
    for i in range(num_variants):
        out.append({
            "titulo": f"Problema en {lugar} del {edificio} - {extras[i % len(extras)][:30]}",
            "descripcion": f"{base_desc} {extras[i]}.",
            "sede": "Sede Norte" if random.random() < 0.6 else "Sede Sur",
            "facultad": random.choice(["Ingenieria", "Administracion", "Ciencias", "Educacion", "Salud"]),
            "anonima": True,
        })
    return out


def post_queja(payload: dict, *, anonima: bool = False) -> dict:
    """POST a queja to the API."""
    body = {
        "titulo": payload["titulo"],
        "descripcion": payload["descripcion"],
        "categoriaDeclarada": payload["categoriaDeclarada"],
        "anonima": anonima or payload.get("anonima", False),
    }
    if payload.get("sede"):
        body["sede"] = payload["sede"]
    if payload.get("facultad"):
        body["facultad"] = payload["facultad"]
    if not body["anonima"] and payload.get("reportante_email"):
        body["contactoEmail"] = payload["reporto_email"] if False else payload["reportante_email"]
    if payload.get("cursoCodigo"):
        body["cursoCodigo"] = payload["cursoCodigo"]
    return {
        "status": (r := requests.post(
            f"{API_BASE}/api/quejas",
            headers={"Content-Type": "application/json", "X-Tenant-ID": TENANT},
            json=body,
            timeout=30,
        )).status_code,
        "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count-infra", type=int, default=10)
    parser.add_argument("--count-acoso", type=int, default=2)
    parser.add_argument("--count-academica", type=int, default=2)
    parser.add_argument("--count-administrativa", type=int, default=1)
    parser.add_argument("--count-salud", type=int, default=1)
    parser.add_argument("--no-infra", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print("Sentinel AcademIA - End-to-End Test (varied content)")
    print(f"API: {API_BASE}")
    print(f"Tenant: {TENANT} (UTEC)")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    submitted = []

    def run(label, items, anonima=False):
        print(f"[{label}] Enviando {len(items)} quejas...")
        for i, queja in enumerate(items, 1):
            result = post_queja(queja, anonima=anonima)
            status = "OK" if result["status"] == 202 else "ERR"
            cat = queja.get("categoriaDeclarada", "?")
            print(f"  [{i:2d}/{len(items)}] {status} HTTP {result['status']} - {queja['titulo'][:55]}")
            if result["status"] == 202:
                submitted.append({"categoria": cat, "quejaId": result["body"].get("quejaId")})
            time.sleep(0.25)
        print()

    if not args.no_infra:
        run(f"INFRAESTRUCTURA x{args.count_infra}",
            [{**q, "categoriaDeclarada": "INFRAESTRUCTURA"} for q in random_infraestructura(args.count_infra)],
            anonima=True)
    run(f"ACOSO x{args.count_acoso}",
        [{**q, "categoriaDeclarada": "ACOSO"} for q in [random_acoso() for _ in range(args.count_acoso)]])
    run(f"ACADEMICA x{args.count_academica}",
        [{**q, "categoriaDeclarada": "ACADEMICA"} for q in [random_academica() for _ in range(args.count_academica)]])
    run(f"ADMINISTRATIVA x{args.count_administrativa}",
        [{**q, "categoriaDeclarada": "ADMINISTRATIVA"} for q in [random_administrativa() for _ in range(args.count_administrativa)]])
    run(f"SALUD x{args.count_salud}",
        [{**q, "categoriaDeclarada": "SALUD"} for q in [random_salud() for _ in range(args.count_salud)]])

    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    from collections import Counter
    counter = Counter(r["categoria"] for r in submitted)
    for cat, count in sorted(counter.items()):
        print(f"  {cat}: {count}")
    print(f"  TOTAL: {len(submitted)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
