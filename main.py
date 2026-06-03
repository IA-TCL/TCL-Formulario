import os
from urllib.parse import quote

import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# --- Configuracion (se lee de variables de entorno en Render) ---
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appLVSEg1Y2zIwvuM")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE", "")  # nombre de la tabla, ej: "Respuestas"


def geolocalizar(request: Request) -> dict:
    """Obtiene la ubicacion del visitante a partir de su IP."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        user_ip = forwarded.split(",")[0].strip()
    else:
        user_ip = request.client.host

    try:
        return requests.get(
            f"https://ipapi.co/{user_ip}/json/",
            timeout=5,
        ).json()
    except Exception:
        return {}


@app.get("/form", response_class=HTMLResponse)
async def form():
    """Muestra el formulario propio. La ubicacion NO aparece aqui."""
    return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Formulario</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
            background: #f4f5f7; margin: 0; padding: 24px;
            display: flex; justify-content: center;
        }
        form {
            background: #fff; padding: 32px; border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,.08);
            width: 100%; max-width: 480px;
        }
        h1 { font-size: 22px; margin: 0 0 24px; color: #1f2937; }
        label { display: block; font-size: 14px; font-weight: 600;
                color: #374151; margin: 16px 0 6px; }
        input {
            width: 100%; padding: 11px 12px; font-size: 15px;
            border: 1px solid #d1d5db; border-radius: 8px;
        }
        input:focus { outline: none; border-color: #2563eb;
                      box-shadow: 0 0 0 3px rgba(37,99,235,.15); }
        button {
            margin-top: 24px; width: 100%; padding: 12px;
            font-size: 16px; font-weight: 600; color: #fff;
            background: #2563eb; border: none; border-radius: 8px; cursor: pointer;
        }
        button:hover { background: #1d4ed8; }
    </style>
</head>
<body>
    <form action="/submit" method="post">
        <h1>Solicitud de trabajo</h1>

        <label for="nombre">Nombre</label>
        <input id="nombre" name="nombre" type="text" required>

        <label for="apellidos">Apellidos</label>
        <input id="apellidos" name="apellidos" type="text" required>

        <label for="correo">Correo electrónico</label>
        <input id="correo" name="correo" type="email" required>

        <label for="celular">Celular</label>
        <input id="celular" name="celular" type="tel" required>

        <button type="submit">Enviar</button>
    </form>
</body>
</html>"""


@app.post("/submit")
async def submit(
    request: Request,
    nombre: str = Form(...),
    apellidos: str = Form(...),
    correo: str = Form(...),
    celular: str = Form(...),
):
    """Recibe el formulario, anade la ubicacion por detras y guarda en Airtable."""
    geo = geolocalizar(request)

    fields = {
        # Campos visibles que rellena la persona
        "Nombre": nombre,
        "Apellidos": apellidos,
        "Correo electrónico": correo,
        "Celular": celular,
        # Ubicacion anadida en el servidor (el usuario nunca la ve)
        "city": geo.get("city"),
        "region": geo.get("region"),
        "country": geo.get("country_name"),
        "ip": geo.get("ip"),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
    }
    # Quitamos los campos sin valor para no enviarlos vacios.
    fields = {k: v for k, v in fields.items() if v is not None}

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{quote(AIRTABLE_TABLE)}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"fields": fields, "typecast": True}

    debug_info = (
        f"URL: {url}\n"
        f"BASE_ID: {AIRTABLE_BASE_ID}\n"
        f"TABLE: {AIRTABLE_TABLE}\n"
        f"TOKEN configurado: {'SI' if AIRTABLE_TOKEN else 'NO'}\n"
        f"Campos enviados: {fields}"
    )

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as exc:
        print("EXCEPCION al llamar Airtable:", exc)
        return HTMLResponse(
            f"<h2>Excepcion al conectar con Airtable</h2>"
            f"<pre>{exc}</pre>"
            f"<hr><pre>{debug_info}</pre>",
            status_code=500,
        )

        if resp.status_code not in (200, 201):
            print("ERROR Airtable:", resp.status_code, resp.text)
        
        return HTMLResponse(
            f"<h2>Error Airtable {resp.status_code}</h2>"
            f"<pre>{resp.text}</pre>"
            f"<hr><pre>{debug_info}</pre>",
            status_code=500,
        )

    return RedirectResponse("/gracias", status_code=303)


@app.get("/gracias", response_class=HTMLResponse)
async def gracias():
    return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>¡Gracias!</title>
    <style>
        body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
               background: #f4f5f7; margin: 0; height: 100vh;
               display: flex; align-items: center; justify-content: center; }
        .card { background: #fff; padding: 40px; border-radius: 12px; text-align: center;
                box-shadow: 0 2px 12px rgba(0,0,0,.08); }
        h1 { color: #16a34a; margin: 0 0 8px; }
        p { color: #4b5563; margin: 0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>¡Gracias!</h1>
        <p>Tu información se ha enviado correctamente.</p>
    </div>
</body>
</html>"""
