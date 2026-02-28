from flask import Flask, render_template, request
from datetime import date
import calendar

app = Flask(__name__)

emociones = []

@app.route("/", methods=["GET", "POST"])
def index():
    emocion = None
    if request.method == "POST":
        emocion = request.form.get("mood")
        nota = request.form.get("nota")
        hoy = date.today().isoformat()

        emociones.append({
            "fecha": hoy,
            "emocion": emocion,
            "nota": nota
        })

    return render_template("index.html", emocion=emocion)


@app.route("/calendario")
def calendario_view():
    hoy = date.today()
    year = hoy.year
    month = hoy.month

    cal = calendar.monthcalendar(year, month)

    emociones_por_dia = {}
    for e in emociones:
        dia = int(e["fecha"].split("-")[2])
        emociones_por_dia[dia] = e["emocion"]

    return render_template(
        "calendario.html",
        calendario=cal,
        emociones=emociones_por_dia,
        mes=month,
        anio=year
    )


if __name__ == "__main__":
    app.run(debug=True)