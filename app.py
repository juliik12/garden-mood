from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for

import calendar
import json
import os
from datetime import date, timedelta
import re
import threading
import time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


secret = os.getenv("SECRET_KEY")
if not secret:
    raise RuntimeError("SECRET_KEY no configurada en variables de entorno")
app.secret_key = secret

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# ✅ Rutas absolutas para JSON (evita problemas de working directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
EMOCIONES_FILE = os.path.join(BASE_DIR, "emociones.json")

# ✅ Lock para evitar corrupción por escrituras simultáneas
JSON_LOCK = threading.Lock()

# ✅ Rate limit simple para login (por IP)
LOGIN_ATTEMPTS = {}  # ip -> [timestamps]
MAX_ATTEMPTS_PER_MIN = 8
WINDOW_SECONDS = 60


def cargar_json(path):
    with JSON_LOCK:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Si se corrompe el JSON por algún motivo, evitamos crashear
                return {}


def guardar_json(path, data):
    with JSON_LOCK:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def rate_limit_login():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    now = time.time()
    arr = LOGIN_ATTEMPTS.get(ip, [])
    arr = [t for t in arr if now - t < WINDOW_SECONDS]
    if len(arr) >= MAX_ATTEMPTS_PER_MIN:
        return True
    arr.append(now)
    LOGIN_ATTEMPTS[ip] = arr
    return False


def normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def validar_fecha(fecha: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha or ""))

def fechas_unicas(user_emociones):
    # set de fechas únicas (YYYY-MM-DD)
    return {e.get("fecha") for e in user_emociones if e.get("fecha")}

def calcular_racha_hasta(fecha_inicio: date, fechas_set: set[str]) -> int:
    racha = 0
    d = fecha_inicio
    while d.isoformat() in fechas_set:
        racha += 1
        d -= timedelta(days=1)
    return racha

def calcular_estado_racha(user_emociones):
    fechas_set = fechas_unicas(user_emociones)
    hoy = date.today()
    hoy_str = hoy.isoformat()

    hoy_cumplido = hoy_str in fechas_set

    # Si hoy cumplió: racha desde hoy
    # Si hoy NO cumplió: racha desde ayer (queda "gris")
    base_fecha = hoy if hoy_cumplido else (hoy - timedelta(days=1))
    racha = calcular_racha_hasta(base_fecha, fechas_set)

    return racha, hoy_cumplido

def limite_por_racha(racha: int) -> int:
    base = 5
    bonus = min(racha // 3, 3)  # +1 cada 3 días, máximo +3
    return base + bonus
# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect("/")

    if request.method == "POST":
        if rate_limit_login():
            return "Demasiados intentos. Probá de nuevo en 1 minuto.", 429

        email = normalizar_email(request.form.get("email"))
        password = request.form.get("password") or ""

        if not email or not password:
            return render_template("login.html", error="Completá email y contraseña")

        users = cargar_json(USERS_FILE)

        if email in users and check_password_hash(users[email]["password"], password):
            session["user"] = email
            return redirect("/")
        else:
            return render_template("login.html", error="Correo o contraseña incorrectos")

    return render_template("login.html", error=None)


# REGISTRO
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if "user" in session:
        return redirect("/")

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        email = normalizar_email(request.form.get("email"))
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not nombre or not email or not password or not confirm:
            return render_template("register.html", error="Completá todos los campos")

        if password != confirm:
            return render_template("register.html", error="Las contraseñas no coinciden")

        if len(password) < 6:
            return render_template("register.html", error="La contraseña debe tener mínimo 6 caracteres")

        users = cargar_json(USERS_FILE)
        if email in users:
            return render_template("register.html", error="El correo ya está registrado")

        users[email] = {"nombre": nombre, "password": generate_password_hash(password)}
        guardar_json(USERS_FILE, users)

        session["user"] = email
        return redirect("/")

    return render_template("register.html", error=None)


# LOGOUT
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user = session["user"]
    hoy = date.today().isoformat()

    emociones_data = cargar_json(EMOCIONES_FILE)
    user_emociones = emociones_data.get(user, [])

    flores_hoy = [e for e in user_emociones if e.get("fecha") == hoy]
    cantidad_hoy = len(flores_hoy)

    
    racha, hoy_cumplido = calcular_estado_racha(user_emociones)

    
    limite_diario = limite_por_racha(racha)

    if request.method == "POST":
        if cantidad_hoy >= limite_diario:
            return redirect("/")

        mood = request.form["mood"]
        nota = request.form["nota"]
        imagen = request.form["imagen"]

        user_emociones.append({
            "emocion": mood,
            "nota": nota,
            "imagen": imagen,
            "fecha": hoy
        })
        racha, hoy_cumplido = calcular_estado_racha(user_emociones)

        emociones_data[user] = user_emociones
        guardar_json(EMOCIONES_FILE, emociones_data)

        return redirect("/")

    return render_template(
        "index.html",
        fecha=hoy,
        cantidad_hoy=cantidad_hoy,
        racha=racha,
        hoy_cumplido=hoy_cumplido,
        limite_diario=limite_diario
        )


@app.route("/calendario")
@login_required
def calendario_view():
    user = session["user"]
    hoy = date.today()
    fecha_hoy = hoy.isoformat()

    year = request.args.get("year", hoy.year, type=int)
    month = request.args.get("month", hoy.month, type=int)

    # Validación liviana
    if year < 1970 or year > 2100 or month < 1 or month > 12:
        return "Parámetros inválidos", 400

    cal = calendar.monthcalendar(year, month)

    emociones_data = cargar_json(EMOCIONES_FILE)
    user_emociones = emociones_data.get(user, [])

    emociones_por_dia = {}
    for e in user_emociones:
        try:
            y, m, d = map(int, (e.get("fecha") or "").split("-"))
        except Exception:
            continue
        if y == year and m == month:
            emociones_por_dia.setdefault(d, []).append(e)

    meses_con_flores = sorted(
        {(int(e["fecha"].split("-")[0]), int(e["fecha"].split("-")[1])) for e in user_emociones if "fecha" in e}
    )
    prev = None
    for y_, m_ in reversed(meses_con_flores):
        if (y_, m_) < (year, month):
            prev = (y_, m_)
            break

    if month == 12:
        next_month = (year + 1, 1)
    else:
        next_month = (year, month + 1)

    if next_month[0] > hoy.year or (next_month[0] == hoy.year and next_month[1] > hoy.month):
        next_month = None

    return render_template(
        "calendario.html",
        calendario=cal,
        emociones=emociones_por_dia,
        mes=month,
        anio=year,
        hoy=hoy.day,
        hoy_fecha=hoy,
        fecha=fecha_hoy,
        prev=prev,
        next_month=next_month,
    )


@app.route("/jardin/<fecha>")
@login_required
def jardin_dia(fecha):
    if not validar_fecha(fecha):
        return "Fecha inválida", 400

    user = session["user"]
    hoy = date.today().isoformat()

    emociones_data = cargar_json(EMOCIONES_FILE)
    user_emociones = emociones_data.get(user, [])

    emociones_dia = [e for e in user_emociones if e.get("fecha") == fecha]
    es_hoy = (fecha == hoy)

    return render_template(
        "jardin.html",
        emociones=emociones_dia,
        fecha=fecha,
        es_hoy=es_hoy,
        cantidad=len(emociones_dia),
    )


if __name__ == "__main__":
    
    app.run()