from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for
from datetime import date
import calendar
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "scrypt:32768:8:1$mYpw7RH1xR5m7wsV$bad3329bd78ee04ddd42e2dacb7198984459b0952588b693c53271f11aefa621c9c35a70a08ae5b96a58359cc3188723589dff8a0d57f3c30e8d" 

USERS_FILE = "users.json"
EMOCIONES_FILE = "emociones.json"


def cargar_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path, "r") as f:
        return json.load(f)

def guardar_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

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
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            return render_template("register.html", error="Las contraseñas no coinciden")

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
    return redirect(url_for('login'))

# PÁGINA PRINCIPAL
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user = session["user"]
    hoy = date.today().isoformat()
    
    emociones_data = cargar_json(EMOCIONES_FILE)
    user_emociones = emociones_data.get(user, [])

    flores_hoy = [e for e in user_emociones if e["fecha"] == hoy]
    cantidad_hoy = len(flores_hoy)

    if request.method == "POST":
        if cantidad_hoy >= 5:
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

        emociones_data[user] = user_emociones
        guardar_json(EMOCIONES_FILE, emociones_data)

        return redirect("/")

    return render_template("index.html", fecha=hoy, cantidad_hoy=cantidad_hoy)


@app.route("/calendario")
@login_required
def calendario_view():
    user = session["user"]
    hoy = date.today()
    fecha_hoy = hoy.isoformat()

    year = request.args.get("year", hoy.year, type=int)
    month = request.args.get("month", hoy.month, type=int)

    cal = calendar.monthcalendar(year, month)

    emociones_data = cargar_json(EMOCIONES_FILE)
    user_emociones = emociones_data.get(user, [])

    emociones_por_dia = {}
    for e in user_emociones:
        y, m, d = map(int, e["fecha"].split("-"))
        if y == year and m == month:
            emociones_por_dia.setdefault(d, []).append(e)


    meses_con_flores = sorted(
        {(int(e["fecha"].split("-")[0]), int(e["fecha"].split("-")[1])) for e in user_emociones}
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

    hoy_fecha = hoy 

    return render_template(
        "calendario.html",
        calendario=cal,
        emociones=emociones_por_dia,
        mes=month,
        anio=year,
        hoy=hoy.day,
        hoy_fecha=hoy_fecha,
        fecha=fecha_hoy,  
        prev=prev,
        next_month=next_month
    )

@app.route("/jardin/<fecha>")
@login_required
def jardin_dia(fecha):
    user = session["user"]
    hoy = date.today().isoformat()

    emociones_data = cargar_json(EMOCIONES_FILE)
    user_emociones = emociones_data.get(user, [])

    emociones_dia = [e for e in user_emociones if e["fecha"] == fecha]

    es_hoy = (fecha == hoy)

    return render_template(
        "jardin.html",
        emociones=emociones_dia,
        fecha=fecha,
        es_hoy=es_hoy,
        cantidad=len(emociones_dia)
    )

if __name__ == "__main__":
    app.run(debug=True)