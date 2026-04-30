"""Low-level Google Sheets read/write primitives used by all tool modules."""

import os
import time
from typing import Any

from dotenv import load_dotenv
import google.auth
from googleapiclient.discovery import build

load_dotenv()

# Simple in-memory cache: {tab_name: (timestamp, rows)}
_cache: dict[str, tuple[float, list[dict]]] = {}
CACHE_TTL = 30  # seconds

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_service = None


def _sheets():
    global _service
    if _service is None:
        creds, _ = google.auth.default(scopes=_SCOPES)
        _service = build("sheets", "v4", credentials=creds)
    return _service.spreadsheets()


def _require(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        raise EnvironmentError(
            f"Variable de entorno '{var}' no configurada. "
            f"Copia .env.example a .env y completa los valores."
        )
    return val


def _col_letter(idx: int) -> str:
    """Convert 0-based column index to A1 notation letter (A, B, ..., Z, AA, ...)."""
    letters = ""
    while True:
        letters = chr(ord("A") + idx % 26) + letters
        idx = idx // 26 - 1
        if idx < 0:
            break
    return letters


def _invalidate(tab_name: str) -> None:
    _cache.pop(tab_name, None)


def read_sheet(tab_name: str, force: bool = False) -> list[dict]:
    """Return all rows of a tab as a list of dicts keyed by header row."""
    now = time.monotonic()
    if not force and tab_name in _cache:
        ts, rows = _cache[tab_name]
        if now - ts < CACHE_TTL:
            return rows

    spreadsheet_id = _require("SPREADSHEET_ID")
    data = _sheets().values().get(
        spreadsheetId=spreadsheet_id, range=tab_name
    ).execute()
    values = data.get("values", [])

    if not values:
        _cache[tab_name] = (now, [])
        return []

    headers = [str(h).strip().lower() for h in values[0]]
    rows = []
    for row_vals in values[1:]:
        padded = list(row_vals) + [""] * (len(headers) - len(row_vals))
        rows.append({h: padded[i] for i, h in enumerate(headers)})

    _cache[tab_name] = (now, rows)
    return rows


def append_row(tab_name: str, row: dict) -> None:
    """Append a new row to the tab. Keys must match the header row exactly."""
    spreadsheet_id = _require("SPREADSHEET_ID")

    hdr_data = _sheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"{tab_name}!1:1"
    ).execute()
    raw_headers = [str(h) for h in (hdr_data.get("values", [[]])[0] if hdr_data else [])]
    values = [str(row.get(h.strip().lower(), "")) for h in raw_headers]

    _sheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [values]},
    ).execute()
    _invalidate(tab_name)


def update_row(tab_name: str, pk_col: str, pk_val: str, updates: dict) -> bool:
    """
    Find the first row where pk_col == pk_val and update the specified columns.
    Returns True if a row was found and updated, False otherwise.
    """
    spreadsheet_id = _require("SPREADSHEET_ID")
    data = _sheets().values().get(
        spreadsheetId=spreadsheet_id, range=tab_name
    ).execute()
    values = data.get("values", [])
    if not values:
        return False

    headers = [str(h).strip().lower() for h in values[0]]
    if pk_col not in headers:
        return False
    pk_idx = headers.index(pk_col)

    row_num = None
    for i, row_vals in enumerate(values[1:], start=2):  # row 1 is header, spreadsheet is 1-based
        padded = list(row_vals) + [""] * (len(headers) - len(row_vals))
        if str(padded[pk_idx]).lower() == str(pk_val).lower():
            row_num = i
            break

    if row_num is None:
        return False

    for col_name, value in updates.items():
        if col_name not in headers:
            continue
        col_idx = headers.index(col_name)
        cell_range = f"{tab_name}!{_col_letter(col_idx)}{row_num}"
        _sheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=cell_range,
            valueInputOption="USER_ENTERED",
            body={"values": [[str(value)]]},
        ).execute()

    _invalidate(tab_name)
    return True


def find_rows(tab_name: str, filters: dict) -> list[dict]:
    """Return all rows where every key-value pair in filters matches."""
    rows = read_sheet(tab_name)
    result = []
    for row in rows:
        if all(str(row.get(k, "")).lower() == str(v).lower() for k, v in filters.items()):
            result.append(row)
    return result


def generate_id(prefix: str, tab_name: str, id_col: str) -> str:
    """
    Generate the next sequential ID in the format PREFIX-YYYY-NNN.
    Example: generate_id("PAG", "Pagos", "pago_id") -> "PAG-2026-001"
    """
    import datetime

    year = datetime.date.today().year
    rows = read_sheet(tab_name)
    year_prefix = f"{prefix}-{year}-"
    max_seq = 0
    for row in rows:
        val = str(row.get(id_col, ""))
        if val.startswith(year_prefix):
            try:
                seq = int(val[len(year_prefix):])
                max_seq = max(max_seq, seq)
            except ValueError:
                pass
    return f"{year_prefix}{max_seq + 1:03d}"


def get_config_value(key: str) -> Any:
    """Read a value from the Config tab by key."""
    rows = read_sheet("Config")
    for row in rows:
        if str(row.get("clave", "")).lower() == key.lower():
            return row.get("valor", "")
    return None
