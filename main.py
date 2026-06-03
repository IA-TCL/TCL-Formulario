from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import requests

app = FastAPI()

# URL del formulario de Airtable (redireccion directa).
# Los campos ocultos (hide_) SI se guardan con este metodo.
FORM_URL = "https://airtable.com/appLVSEg1Y2zIwvuM/pagwbdSKFwHyLLTTE/form"


@app.get("/form")
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

    return RedirectResponse(
        f"{FORM_URL}?{urlencode(params)}"
    )
