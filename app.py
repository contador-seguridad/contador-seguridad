from flask import Flask, render_template_string, request, redirect, send_file
from datetime import datetime
import sqlite3
from openpyxl import Workbook
import os

app = Flask(__name__)

# ------------------------
# BASE DE DATOS
# ------------------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contador (
        id INTEGER PRIMARY KEY,
        fecha_inicio TEXT,
        record_dias INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        dias INTEGER,
        horas INTEGER,
        minutos INTEGER
    )
    """)

    cursor.execute("SELECT * FROM contador WHERE id = 1")

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO contador (id, fecha_inicio, record_dias) VALUES (1, ?, 0)",
            (datetime.now().isoformat(),)
        )

    conn.commit()
    conn.close()


def obtener_record():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT record_dias FROM contador WHERE id = 1")
    record = cursor.fetchone()[0]
    conn.close()
    return record


def actualizar_record(dias):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE contador SET record_dias = ? WHERE id = 1", (dias,))
    conn.commit()
    conn.close()


def obtener_fecha():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fecha_inicio FROM contador WHERE id = 1")
    fecha = cursor.fetchone()[0]
    conn.close()
    return datetime.fromisoformat(fecha)


def reiniciar():
    fecha_inicio = obtener_fecha()
    ahora = datetime.now()
    diferencia = ahora - fecha_inicio

    dias = diferencia.days
    horas = diferencia.seconds // 3600
    minutos = (diferencia.seconds % 3600) // 60

    record_actual = obtener_record()

    if dias > record_actual:
        actualizar_record(dias)

def borrar_historial():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historial")
    conn.commit()
    conn.close()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO historial (fecha_inicio, fecha_fin, dias, horas, minutos)
        VALUES (?, ?, ?, ?, ?)
    """, (
        fecha_inicio.isoformat(),
        ahora.isoformat(),
        dias,
        horas,
        minutos
    ))

    cursor.execute("UPDATE contador SET fecha_inicio = ? WHERE id = 1",
                   (ahora.isoformat(),))

    conn.commit()
    conn.close()


# ------------------------
# EXPORTAR EXCEL
# ------------------------

@app.route("/exportar")
def exportar_excel():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fecha_inicio, fecha_fin, dias, horas, minutos FROM historial")
    datos = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Historial Accidentes"

    ws.append(["Fecha Inicio", "Fecha Fin", "Días", "Horas", "Minutos"])

    for fila in datos:
        ws.append(fila)

    archivo = "historial_accidentes.xlsx"
    wb.save(archivo)

    return send_file(archivo, as_attachment=True)

@app.route("/borrar", methods=["POST"])
def ruta_borrar():

    if not session.get("admin"):
        return redirect("/admin")

    borrar_historial()
    return redirect("/panel")


# ------------------------
# RUTA PRINCIPAL
# ------------------------

@app.route("/")
def home():
    fecha_inicio = obtener_fecha()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Contador Seguridad</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
*{
    box-sizing:border-box;
}

body{
    margin:0;
    min-height:100dvh;
    background:radial-gradient(circle at center,#001a1f,#002b36,#001018);
    font-family:'Segoe UI',sans-serif;
    display:flex;
    justify-content:center;
    align-items:center;
    color:#dff;
    padding:20px;
}

.panel{
    width:100%;
    max-width:900px;
    text-align:center;
    padding:clamp(20px,5vw,50px);
    border-radius:25px;
    background:#111c2d;
    box-shadow:0 20px 60px rgba(0,0,0,0.5);
}

.titulo-seccion{
    font-size:clamp(16px,3vw,28px);
    letter-spacing:3px;
    text-transform:uppercase;
    color:#93c5fd;
    margin:20px 0;
}

#contador{
    font-size:clamp(36px,8vw,110px);
    font-weight:bold;
    letter-spacing:4px;
    color:#00ff88;
    margin:30px 0;
    transition:transform 0.3s ease;
    word-wrap:break-word;
}

.hidden-admin{
    position:fixed;
    bottom:10px;
    right:10px;
    width:40px;
    height:40px;
    cursor:pointer;
    opacity:0.05;
}
</style>
</head>
<body>

<div class="panel">

    <div class="titulo-seccion">Bienvenidos</div>
    <div class="titulo-seccion">Hoy cumplimos</div>

    <div id="contador"></div>

    <div class="titulo-seccion">Sin accidentes</div>
    <div class="titulo-seccion">Récord histórico: {{record}} días</div>
    <div class="titulo-seccion">Nuestro objetivo es Cero Accidentes</div>

</div>

<div class="hidden-admin" ondblclick="window.location='/admin'"></div>

<script>
let inicio = new Date("{{ fecha_inicio }}").getTime();
let ultimoDia = 0;

function digitalBeep(){
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(1200, ctx.currentTime);
    gain.gain.setValueAtTime(0.05, ctx.currentTime);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.15);
}

setInterval(function(){
    let ahora = new Date().getTime();
    let diff = ahora - inicio;

    let dias = Math.floor(diff/(1000*60*60*24));
    let horas = Math.floor((diff/(1000*60*60))%24);
    let minutos = Math.floor((diff/(1000*60))%60);

    document.getElementById("contador").innerHTML =
        dias+" DÍAS · "+horas+" HRS · "+minutos+" MIN";

    if(dias>ultimoDia){
        ultimoDia=dias;
        let contador = document.getElementById("contador");
        contador.style.transform="scale(1.1)";
        setTimeout(()=>{contador.style.transform="scale(1)";},300);
        digitalBeep();
    }

},1000);
</script>

</body>
</html>
""", 
fecha_inicio=fecha_inicio.isoformat(),
record=obtener_record()
)


# ------------------------
# ADMIN
# ------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            reiniciar()
            return redirect("/admin")

    return """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    body{
        background:#0f172a;
        font-family:Segoe UI;
        color:white;
        text-align:center;
        padding:50px 20px;
    }
    input,button{
        padding:12px 18px;
        margin:10px;
        border-radius:10px;
        border:none;
        width:90%;
        max-width:300px;
        font-size:16px;
    }
    button{
        background:#00b894;
        color:white;
        cursor:pointer;
    }
    a{
        display:block;
        margin-top:20px;
        color:#66ccff;
        text-decoration:none;
    }
    </style>
    </head>
    <body>

    <h2>Panel Administrador</h2>

    <form method="post">
        <input type="password" name="password" placeholder="Contraseña">
        <br>
        <button type="submit">Reiniciar por Accidente</button>
    </form>

    <a href="/exportar">Descargar Historial en Excel</a>
    <a href="/">Volver al Contador</a>

    </body>
    </html>
    """


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000,)