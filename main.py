from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from urllib.parse import urlencode
import requests

app = FastAPI()

# URL de EMBED del formulario (con /embed/, no solo /form).
# Se obtiene en Airtable: "Share form" -> "Embed this form on your site".
EMBED_URL = "https://airtable.com/embed/appLVSEg1Y2zIwvuM/pagwbdSKFwHyLLTTE/form"


@app.get("/form", response_class=HTMLResponse)
async def form(request: Request):

    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        user_ip = forwarded.split(",")[0].strip()
    else:
        user_ip = request.client.host

    try:
        geo = requests.get(
            f"https://ipapi.co/{user_ip}/json/",
            timeout=5
        ).json()
    except Exception:
        geo = {}

    params = {
        "prefill_city": geo.get("city"),
        "prefill_region": geo.get("region"),
        "prefill_country": geo.get("country_name"),
        "prefill_ip": geo.get("ip"),
        "prefill_latitude": geo.get("latitude"),
        "prefill_longitude": geo.get("longitude"),

        "hide_city": "true",
        "hide_region": "true",
        "hide_country": "true",
        "hide_ip": "true",
        "hide_latitude": "true",
        "hide_longitude": "true"
    }

    # Quitamos los valores None para no enviar "None" como texto en la URL.
    params = {k: v for k, v in params.items() if v is not None}

    iframe_src = f"{EMBED_URL}?{urlencode(params)}"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Formulario</title>
    <style>
        html, body {{ margin: 0; height: 100%; }}
        iframe {{ width: 100%; height: 100vh; border: 0; }}
    </style>
</head>
<body>
    <iframe src="{iframe_src}"
            sandbox="allow-scripts allow-forms allow-same-origin allow-popups">
    </iframe>
</body>
</html>"""
