import os
from urllib.parse import quote

import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Configuracion (se lee de variables de entorno en Render) ---
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appLVSEg1Y2zIwvuM")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE", "")  # nombre de la tabla, ej: "Respuestas"


def geolocalizar(request: Request) -> dict:
    """Obtiene la ubicación del visitante usando múltiples proveedores de respaldo."""

    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        user_ip = forwarded.split(",")[0].strip()
    else:
        user_ip = request.client.host

    proveedores = [
        {
            "nombre": "ipwho.is",
            "url": f"https://ipwho.is/{user_ip}",
            "parser": lambda d: {
                "city": d.get("city"),
                "region": d.get("region"),
                "country_name": d.get("country"),
                "ip": d.get("ip"),
                "latitude": d.get("latitude"),
                "longitude": d.get("longitude"),
            },
        },
        {
            "nombre": "ip-api",
            "url": f"http://ip-api.com/json/{user_ip}",
            "parser": lambda d: {
                "city": d.get("city"),
                "region": d.get("regionName"),
                "country_name": d.get("country"),
                "ip": d.get("query"),
                "latitude": d.get("lat"),
                "longitude": d.get("lon"),
            },
        },
        {
            "nombre": "ipinfo",
            "url": f"https://ipinfo.io/{user_ip}/json",
            "parser": lambda d: {
                "city": d.get("city"),
                "region": d.get("region"),
                "country_name": d.get("country"),
                "ip": d.get("ip"),
                "latitude": (
                    d.get("loc", "").split(",")[0]
                    if d.get("loc")
                    else None
                ),
                "longitude": (
                    d.get("loc", "").split(",")[1]
                    if d.get("loc")
                    else None
                ),
            },
        },
        {
            "nombre": "ipapi",
            "url": f"https://ipapi.co/{user_ip}/json/",
            "parser": lambda d: {
                "city": d.get("city"),
                "region": d.get("region"),
                "country_name": d.get("country_name"),
                "ip": d.get("ip"),
                "latitude": d.get("latitude"),
                "longitude": d.get("longitude"),
            },
        },
        {
            "nombre": "geolocation-db",
            "url": f"https://geolocation-db.com/json/{user_ip}",
            "parser": lambda d: {
                "city": d.get("city"),
                "region": d.get("state"),
                "country_name": d.get("country_name"),
                "ip": d.get("IPv4"),
                "latitude": None,
                "longitude": None,
            },
        },
    ]

    for proveedor in proveedores:
        try:
            print(f"Intentando geolocalizar con {proveedor['nombre']}")

            response = requests.get(
                proveedor["url"],
                timeout=2,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            print(
                f"{proveedor['nombre']} STATUS: "
                f"{response.status_code}"
            )

            if response.status_code != 200:
                continue

            data = response.json()

            resultado = proveedor["parser"](data)

            if resultado.get("ip"):
                print(
                    f"Geolocalización obtenida desde "
                    f"{proveedor['nombre']}"
                )

                return {
                    "city": resultado.get("city"),
                    "region": resultado.get("region"),
                    "country_name": resultado.get("country_name"),
                    "ip": resultado.get("ip"),
                    "latitude": resultado.get("latitude"),
                    "longitude": resultado.get("longitude"),
                }

        except Exception as e:
            print(
                f"Error con {proveedor['nombre']}: {e}"
            )

    print("Ningún proveedor respondió correctamente")

    return {}


@app.get("/test-geo")
async def test_geo():
    import requests

    urls = [
        "https://ipwho.is/8.8.8.8",
        "http://ip-api.com/json/8.8.8.8",
        "https://ipinfo.io/8.8.8.8/json",
        "https://ipapi.co/8.8.8.8/json/",
        "https://geolocation-db.com/json/8.8.8.8",
    ]

    resultados = {}

    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            resultados[url] = {
                "status": r.status_code,
                "ok": True,
            }
        except Exception as e:
            resultados[url] = {
                "ok": False,
                "error": str(e),
            }

    return resultados


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
            background: #2A4038;
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
        .logo {
            margin-bottom: 28px; 
        }

        .logo-img {
            height: auto;
            width: 180px;
            display: block;
        }
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
            font-style: italic;
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
            <img src="/static/logo.png" alt="TCI" class="logo-img">
        </div>

        <h1>Registro de Lugar de Trabajo e Inicio de Jornada</h1>
        <p class="subtitle" style="font-style: italic;">Complete el formulario para reportar su ingreso y lugar de trabajo al inicio de la jornada.</p>

        <hr>

        <form action="/submit" method="post">
            <div class="grid">
                <div class="field">
                    <label for="nombre">Nombres</label>
                    <p class="hint" style="font-style: italic;">Ingrese su nombre o nombres.</p>
                    <input id="nombre" name="nombre" type="text" required>
                </div>
                <div class="field">
                    <label for="apellidos">Apellidos</label>
                    <p class="hint" style="font-style: italic;">Ingrese sus apellidos completos.</p>
                    <input id="apellidos" name="apellidos" type="text" required>
                </div>
                <div class="field">
                    <label for="correo"">Correo corporativo</label>
                    <p class="hint" style="font-style: italic;">Ingrese su correo corporativo.</p>
                    <input id="correo" name="correo" type="email" required>
                </div>
                <div class="field">
                    <label for="lugar_trabajo"">Lugar de trabajo</label>
                    <p class="hint" style="font-style: italic;">Especifique si se encuentra trabajando desde casa, una oficina o una sede autorizada.</p>
                    <input id="lugar_trabajo" name="lugar_trabajo" type="text" required>
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
    lugar_trabajo: str = Form(...),
):
    """Recibe el formulario, anade la ubicacion por detras y guarda en Airtable."""
    geo = geolocalizar(request)

    fields = {
        # Campos visibles que rellena la persona
        "Nombre": nombre,
        "Apellidos": apellidos,
        "Correo electrónico": correo,
        "Lugar de trabajo": lugar_trabajo,
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
        print("GEO:", geo)
        print("FIELDS:", fields)    
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
