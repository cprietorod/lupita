"""Tools for managing Colombian tax obligations (impuestos tab)."""

import datetime

from ..sheets import append_row, generate_id, read_sheet, update_row


def get_upcoming_tax_deadlines(days_ahead: int = 60) -> dict:
    """
    Returns all unpaid tax obligations due within the next N days.

    Args:
        days_ahead: Look-ahead window in days. Defaults to 60.

    Returns:
        dict with 'status', 'count', and 'eventos' sorted by fecha_vencimiento.
    """
    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days_ahead)
    rows = read_sheet("impuestos")
    upcoming = []
    for row in rows:
        if str(row.get("estado", "")).upper() == "PAGADO":
            continue
        fecha_str = str(row.get("fecha_vencimiento", ""))
        try:
            fecha = datetime.date.fromisoformat(fecha_str)
        except ValueError:
            continue
        if today <= fecha <= cutoff:
            row = dict(row)
            row["dias_para_vencer"] = (fecha - today).days
            upcoming.append(row)
    upcoming.sort(key=lambda r: r.get("fecha_vencimiento", ""))
    return {"status": "ok", "count": len(upcoming), "eventos": upcoming}


def get_tax_calendar(year: int = 0) -> dict:
    """
    Returns all tax obligations for the given year grouped by tipo.

    Args:
        year: Year to query. Defaults to current year.

    Returns:
        dict with 'status', 'year', 'total', and 'por_tipo'.
    """
    if year == 0:
        year = datetime.date.today().year
    rows = read_sheet("impuestos")
    year_rows = [r for r in rows if str(r.get("anio", "")) == str(year)]

    grouped: dict[str, list] = {}
    for row in year_rows:
        tipo = str(row.get("tipo", "OTRO"))
        grouped.setdefault(tipo, []).append(row)

    return {"status": "ok", "year": year, "total": len(year_rows), "por_tipo": grouped}


def get_predial_info(apt_id: str = "") -> dict:
    """
    Returns predial (property tax) deadlines for all properties or a specific apartment.

    Args:
        apt_id: Specific apartment to query. Empty returns all.

    Returns:
        dict with 'status', 'count', and 'predial' list with deadline info.
    """
    today = datetime.date.today()
    rows = read_sheet("impuestos")
    predial_rows = [r for r in rows if str(r.get("tipo", "")).upper() == "PREDIAL"]
    if apt_id:
        predial_rows = [r for r in predial_rows if str(r.get("apt_id", "")) == apt_id]

    result = []
    for row in predial_rows:
        row = dict(row)
        fecha_str = str(row.get("fecha_vencimiento", ""))
        try:
            fecha = datetime.date.fromisoformat(fecha_str)
            row["dias_para_vencer"] = (fecha - today).days
            row["vencido"] = fecha < today
        except ValueError:
            pass
        result.append(row)

    result.sort(key=lambda r: r.get("fecha_vencimiento", ""))
    return {"status": "ok", "count": len(result), "predial": result}


def mark_tax_paid(
    impuesto_id: str,
    monto: float,
    fecha_pago: str = "",
    notas: str = "",
) -> dict:
    """
    Marks a tax obligation as PAGADO.

    Args:
        impuesto_id: The tax record identifier, e.g. 'IMP-2026-001'.
        monto: Amount paid in COP.
        fecha_pago: Date paid in YYYY-MM-DD. Defaults to today.
        notas: Optional notes.

    Returns:
        dict with 'status' and confirmation message.
    """
    updates: dict = {
        "estado": "PAGADO",
        "monto": monto,
        "fecha_pago": fecha_pago or datetime.date.today().isoformat(),
    }
    if notas:
        updates["notas"] = notas
    updated = update_row("impuestos", "impuesto_id", impuesto_id, updates)
    if not updated:
        return {"status": "not_found", "message": f"Impuesto {impuesto_id} no encontrado."}
    return {"status": "ok", "message": f"Impuesto {impuesto_id} marcado como PAGADO por ${monto:,.0f} COP."}


def add_tax_record(
    apt_id: str,
    tipo: str,
    anio: int,
    fecha_vencimiento: str,
    monto: float = 0.0,
) -> dict:
    """
    Adds a new tax obligation record for an apartment.

    Args:
        apt_id: The apartment identifier.
        tipo: Tax type. Valid: 'PREDIAL', 'RENTA', 'ICA'.
        anio: Tax year, e.g. 2026.
        fecha_vencimiento: Final deadline in YYYY-MM-DD.
        monto: Estimated amount in COP. Defaults to 0.

    Returns:
        dict with 'status' and 'impuesto_id'.
    """
    impuesto_id = generate_id("IMP", "impuestos", "impuesto_id")
    row = {
        "impuesto_id": impuesto_id,
        "apt_id": apt_id,
        "tipo": tipo.upper(),
        "anio": anio,
        "fecha_vencimiento": fecha_vencimiento,
        "monto": monto if monto else "",
        "estado": "PENDIENTE",
        "fecha_pago": "",
        "descuento_aplicado": "",
        "notas": "",
    }
    append_row("impuestos", row)
    return {"status": "ok", "impuesto_id": impuesto_id}
