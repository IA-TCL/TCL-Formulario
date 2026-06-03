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
    <title>Teletrabajo</title>
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #dde3ea;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px 16px;
        }
        .card {
            background: #fff;
            border-radius: 16px;
            padding: 40px 48px 36px;
            width: 100%;
            max-width: 820px;
            box-shadow: 0 4px 28px rgba(0,0,0,.10);
        }
        .logo { margin-bottom: 28px; }
        h1 {
            font-size: 30px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 13px;
            color: #6b7280;
            line-height: 1.55;
            margin-bottom: 28px;
        }
        hr { border: none; border-top: 1px solid #e5e7eb; margin-bottom: 28px; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px 36px;
        }
        .field label {
            display: block;
            font-size: 14px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 4px;
        }
        .field .hint {
            font-size: 12px;
            color: #6b7280;
            line-height: 1.45;
            margin-bottom: 8px;
        }
        .field input {
            width: 100%;
            padding: 10px 12px;
            font-size: 14px;
            border: 1.5px solid #d1d5db;
            border-radius: 7px;
            color: #111827;
            background: #fff;
            transition: border-color .15s, box-shadow .15s;
        }
        .field input:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37,99,235,.12);
        }
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 32px;
        }
        .btn-clear {
            background: none;
            border: none;
            color: #2563eb;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 0;
            font-family: inherit;
        }
        .btn-clear:hover { text-decoration: underline; }
        .btn-submit {
            background: #111827;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 11px 32px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            transition: background .15s;
        }
        .btn-submit:hover { background: #1f2937; }
        @media (max-width: 580px) {
            .card { padding: 28px 20px 24px; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="card">
        <!-- Logo TCI -->
        <div class="logo">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 76" width="210" height="80" aria-label="TCI">
                <!-- ESPIRAL: 4 arcos de 270° entrelazados, centro (36,40), radio 23 -->
                <!-- Gris (fondo) -->
                <path d="M 59 40 A 23 23 0 1 1 36 17" fill="none" stroke="#8195a4" stroke-width="9" stroke-linecap="round"/>
                <!-- Verde claro (rotado 90°) -->
                <path d="M 59 40 A 23 23 0 1 1 36 17" fill="none" stroke="#8dd09b" stroke-width="9" stroke-linecap="round" transform="rotate(90 36 40)"/>
                <!-- Menta (rotado 180°) -->
                <path d="M 59 40 A 23 23 0 1 1 36 17" fill="none" stroke="#7ec8bf" stroke-width="9" stroke-linecap="round" transform="rotate(180 36 40)"/>
                <!-- Verde oscuro (frente, rotado 270°) -->
                <path d="M 59 40 A 23 23 0 1 1 36 17" fill="none" stroke="#143828" stroke-width="9" stroke-linecap="round" transform="rotate(270 36 40)"/>
                <!-- T: cuadrado acento, barra horizontal, palo vertical -->
                <rect x="87" y="7"  width="8"  height="8"  fill="#143828"/>
                <rect x="79" y="18" width="34" height="7"  fill="#143828"/>
                <rect x="93" y="25" width="7"  height="41" fill="#143828"/>
                <!-- C: semicirculo gris, abre a la derecha -->
                <path d="M 145 18 A 25 25 0 0 0 145 68" fill="none" stroke="#8195a4" stroke-width="8" stroke-linecap="butt"/>
                <!-- I: barra vertical gris -->
                <rect x="161" y="18" width="8" height="50" fill="#8195a4"/>
                <!-- Punto: cuadrado verde oscuro -->
                <rect x="178" y="59" width="10" height="10" fill="#143828"/>
            </svg>
        </div>

        <h1>Teletrabajo</h1>
        <p class="subtitle">Complete la siguiente información, los datos proporcionados serán utilizados únicamente para fines administrativos relacionados con la evaluación y gestión de esta solicitud.</p>

        <hr>

        <form action="/submit" method="post">
            <div class="grid">
                <div class="field">
                    <label for="nombre">Nombre</label>
                    <p class="hint">Ingrese su nombre o nombres.</p>
                    <input id="nombre" name="nombre" type="text" required>
                </div>
                <div class="field">
                    <label for="apellidos">Apellidos</label>
                    <p class="hint">Ingrese sus apellidos completos.</p>
                    <input id="apellidos" name="apellidos" type="text" required>
                </div>
                <div class="field">
                    <label for="correo">Correo electrónico</label>
                    <p class="hint">Ingrese un correo electrónico activo donde podamos enviar información y notificaciones relacionadas con su solicitud.</p>
                    <input id="correo" name="correo" type="email" required>
                </div>
                <div class="field">
                    <label for="celular">Celular</label>
                    <p class="hint">Ingrese un número de celular actualizado para facilitar el contacto y seguimiento de la solicitud.</p>
                    <input id="celular" name="celular" type="tel" required>
                </div>
            </div>

            <div class="footer">
                <button type="reset" class="btn-clear">&#8635; Borrar formulario</button>
                <button type="submit" class="btn-submit">Enviar</button>
            </div>
        </form>
    </div>
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
