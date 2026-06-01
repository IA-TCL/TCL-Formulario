from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import requests

app = FastAPI()

FORM_URL = "https://airtable.com/appLVSEg1Y2zIwvuM/pagwbdSKFwHyLLTTE/form"

@app.get("/form")
async def form(request: Request):

    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        user_ip = forwarded.split(",")[0].strip()
    else:
        user_ip = request.client.host

    geo = requests.get(
        f"https://ipapi.co/{user_ip}/json/"
    ).json()

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

    return RedirectResponse(
        f"{FORM_URL}?{urlencode(params)}"
    )