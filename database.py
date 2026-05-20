import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def supabase_get(table: str, params: dict = None):
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def supabase_post(table: str, data: dict | list):
    r = httpx.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, json=data, timeout=30)
    r.raise_for_status()
    return r.json()


def supabase_patch(table: str, params: dict, data: dict):
    r = httpx.patch(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params, json=data, timeout=30)
    r.raise_for_status()
    return r.json()


def supabase_head(table: str, params: dict = None):
    """Get count using HEAD + Prefer: count=exact"""
    h = {**HEADERS, "Prefer": "count=exact"}
    r = httpx.head(f"{SUPABASE_URL}/rest/v1/{table}", headers=h, params=params or {}, timeout=30)
    r.raise_for_status()
    content_range = r.headers.get("content-range", "*/0")
    return int(content_range.split("/")[-1])
