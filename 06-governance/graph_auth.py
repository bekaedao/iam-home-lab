import os
import msal
import requests
from dotenv import load_dotenv

load_dotenv()
TENANT_ID = os.environ["TENANT_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
GRAPH = "https://graph.microsoft.com/v1.0"


def get_token():
    """Sign in as the app (client credentials flow) and return an access token."""
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise SystemExit(f"Token error: {result.get('error')} - {result.get('error_description')}")
    return result["access_token"]


def headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}


def check(r):
    """Stop with Graph's real error message instead of a vague one."""
    if not r.ok:
        raise SystemExit(f"Graph error {r.status_code}: {r.text}")
    return r


def get_all(url):
    """Follow @odata.nextLink so we get every page of results, not just the first."""
    h = headers()
    items = []
    while url:
        data = check(requests.get(url, headers=h, timeout=30)).json()
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return items