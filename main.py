import os
from pathlib import Path
from urllib.parse import quote

import requests
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

TEMPLATES = Path("templates")


@app.api_route("/", methods=["GET", "HEAD"])
async def root(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    return RedirectResponse("/form")

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
    return (TEMPLATES / "form.html").read_text(encoding="utf-8")


@app.post("/submit")
async def submit(
    request: Request,
    nombre: str = Form(...),
    apellidos: str = Form(...),
    correo: str = Form(...),
    tipo_novedad: str = Form(...),
):
    """Recibe el formulario, anade la ubicacion por detras y guarda en Airtable."""
    geo = geolocalizar(request)

    fields = {
        # Campos visibles que rellena la persona
        "Nombres": nombre,
        "Apellidos": apellidos,
        "Correo corporativo": correo,
        "Tipo de novedad": tipo_novedad,
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
    return (TEMPLATES / "gracias.html").read_text(encoding="utf-8")
