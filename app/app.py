"""
Aplicación web con inicio de sesión (Flask + PostgreSQL).

- Valida usuario y contraseña contra la tabla `usuarios` (hash bcrypt).
- Consultas parametrizadas (sin concatenar strings -> evita SQL injection).
- Toda la configuración sensible se lee de variables de entorno.
- El panel administrativo (/panel) solo es accesible con sesión iniciada.
"""
import os
import time
import logging
from functools import wraps
from pathlib import Path

import bcrypt
import psycopg
from flask import Flask, render_template, request, redirect, url_for, session, flash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("app")

app = Flask(__name__)

# --- Configuración desde variables de entorno ---------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Falta la variable de entorno SECRET_KEY")
app.secret_key = SECRET_KEY

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,          # JS no puede leer la cookie
    SESSION_COOKIE_SAMESITE="Lax",         # mitiga CSRF básico
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=1800,       # 30 minutos
)


def get_conninfo() -> str:
    """Opción A (Blitz Cloud) define DATABASE_URL; en local se usan variables DB_*."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    return (
        f"host={os.environ.get('DB_HOST', 'db')} "
        f"port={os.environ.get('DB_PORT', '5432')} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )


def get_conn():
    return psycopg.connect(get_conninfo(), connect_timeout=5)


def init_db(retries: int = 15, delay: int = 2):
    """Espera a que la BD esté lista y ejecuta init.sql (idempotente).
    En la nube (Opción A) es lo que crea la tabla y los usuarios de prueba."""
    if os.environ.get("RUN_DB_INIT", "true").lower() != "true":
        return
    sql = (Path(__file__).parent / "init.sql").read_text(encoding="utf-8")
    for intento in range(1, retries + 1):
        try:
            with get_conn() as conn:
                conn.execute(sql)
            log.info("Base de datos inicializada correctamente")
            return
        except psycopg.OperationalError as e:
            log.warning("BD no disponible (intento %s/%s): %s", intento, retries, e)
            time.sleep(delay)
    raise RuntimeError("No se pudo conectar a la base de datos")


init_db()


# --- Datos de demostración del panel (solo visuales) --------------------------
SERVICIOS = [
    {"nombre": "Proxy", "rol": "Nginx, único punto de entrada", "imagen": "nginx:1.27-alpine",
     "puerto": "80, público", "activo": "3 d 4 h", "cpu": 4, "memoria": 12, "protocolo": "HTTP"},
    {"nombre": "Aplicación", "rol": "Flask + Gunicorn", "imagen": "cloud-login-app:1.1.0",
     "puerto": "8000, interno", "activo": "3 d 4 h", "cpu": 23, "memoria": 64, "protocolo": "SQL"},
    {"nombre": "Base de datos", "rol": "PostgreSQL con volumen db_data", "imagen": "postgres:17.2-alpine",
     "puerto": "5432, interno", "activo": "3 d 4 h", "cpu": 11, "memoria": 41},
]

PETICIONES = [
    {"hora": f"{h:02d}:00", "valor": v}
    for h, v in enumerate([182, 141, 118, 96, 88, 104, 190, 412, 786, 1104, 1236, 1298,
                           1180, 1265, 1342, 1310, 1218, 1096, 948, 802, 690, 566, 402, 268])
]

EVENTOS = [
    {"hora": "10:42", "titulo": "Inicio de sesión correcto", "detalle": "admin desde la red interna", "tipo": "ok"},
    {"hora": "10:15", "titulo": "Copia de seguridad completada", "detalle": "Volumen db_data, 12,4 MB", "tipo": "ok"},
    {"hora": "09:58", "titulo": "Memoria alta en la aplicación", "detalle": "Llegó al 78 % durante 4 minutos", "tipo": "aviso"},
    {"hora": "09:30", "titulo": "Despliegue de cloud-login-app:1.1.0", "detalle": "Imagen descargada de Docker Hub", "tipo": "ok"},
    {"hora": "08:02", "titulo": "Base de datos lista", "detalle": "El healthcheck respondió en 3 s", "tipo": "ok"},
]


# --- Utilidades ---------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para ver esa página.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.after_request
def no_cache(resp):
    # Evita que el navegador muestre la página protegida desde caché tras cerrar sesión
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp


# --- Rutas --------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "usuario_id" in session:
            return redirect(url_for("panel"))
        return render_template("login.html")

    usuario = request.form.get("usuario", "").strip()
    password = request.form.get("password", "")

    with get_conn() as conn:
        fila = conn.execute(
            "SELECT id, password_hash, nombre FROM usuarios WHERE usuario = %s",  # parametrizada
            (usuario,),
        ).fetchone()

    if fila and bcrypt.checkpw(password.encode(), fila[1].encode()):
        session.clear()
        session.permanent = True
        session["usuario_id"] = fila[0]
        session["nombre"] = fila[2]
        log.info("Login correcto: %s", usuario)
        return redirect(url_for("panel"))

    log.info("Login fallido: %s", usuario)
    # Mensaje genérico: no revela si el usuario existe
    flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html", usuario=usuario), 401


@app.route("/panel")
@login_required
def panel():
    with get_conn() as conn:
        filas = conn.execute(
            "SELECT usuario, nombre, creado_en FROM usuarios ORDER BY id"
        ).fetchall()
    usuarios = [{"usuario": u, "nombre": n, "creado_en": c} for u, n, c in filas]
    return render_template(
        "panel.html",
        nombre=session["nombre"],
        usuarios=usuarios,
        servicios=SERVICIOS,
        peticiones=PETICIONES,
        total_peticiones=sum(p["valor"] for p in PETICIONES),
        pico=max(PETICIONES, key=lambda p: p["valor"]),
        eventos=EVENTOS,
    )


@app.route("/bienvenida")
def bienvenida():
    # Ruta anterior: se mantiene para no romper enlaces guardados
    return redirect(url_for("panel"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "ok")
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return {"status": "ok"}
