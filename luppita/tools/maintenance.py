"""Tools for tracking apartment repairs and maintenance (reparaciones tab)."""

import datetime

from ..sheets import append_row, read_sheet, update_row

PRIORITY_ORDER = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}

_RESPONSABLE = {
    "ESTRUCTURA": "PROPIETARIO",
    "ELECTRICO": "PROPIETARIO",
    "PLOMERIA": "PROPIETARIO",
    "PINTURA": "PROPIETARIO",
    "ELECTRODOMESTICO": "INQUILINO",
    "OTRO": "PROPIETARIO",
}


def _next_rep_id(rows: list[dict]) -> str:
    max_seq = 0
    for row in rows:
        val = str(row.get("reparacion_id", ""))
        if val.startswith("REP-"):
            try:
                seq = int(val[4:])
                max_seq = max(max_seq, seq)
            except ValueError:
                pass
    return f"REP-{max_seq + 1:03d}"


def get_pending_repairs(apt_id: str = "") -> dict:
    """
    Returns all pending or in-progress repairs, optionally filtered by apartment.
    Flags ALTA priority repairs open more than 7 days as urgente.

    Args:
        apt_id: Filter to a specific apartment. Empty returns all.

    Returns:
        dict with 'status', 'count', and 'pendientes' sorted by priority then date.
    """
    today = datetime.date.today()
    rows = read_sheet("reparaciones")
    pending = [r for r in rows if str(r.get("estado", "")).upper() in ("PENDIENTE", "EN_PROCESO")]
    if apt_id:
        pending = [r for r in pending if str(r.get("apt_id", "")) == apt_id]

    result = []
    for r in pending:
        r = dict(r)
        try:
            dias = (today - datetime.date.fromisoformat(str(r.get("fecha_reporte", "")))).days
        except ValueError:
            dias = 0
        r["dias_pendiente"] = dias
        r["urgente"] = str(r.get("prioridad", "")).upper() == "ALTA" and dias > 7
        result.append(r)

    result.sort(key=lambda r: (
        PRIORITY_ORDER.get(str(r.get("prioridad", "BAJA")).upper(), 2),
        str(r.get("fecha_reporte", "")),
    ))
    return {"status": "ok", "count": len(result), "pendientes": result}


def log_repair(
    apt_id: str,
    descripcion: str,
    tipo: str,
    prioridad: str = "MEDIA",
    costo_estimado: float = 0.0,
) -> dict:
    """
    Logs a new repair. Automatically suggests responsable based on Ley 820 de 2003.

    Args:
        apt_id: The apartment identifier, e.g. 'APT-001'.
        descripcion: Description of the issue.
        tipo: Category. Valid: 'PLOMERIA', 'ELECTRICO', 'PINTURA', 'ESTRUCTURA',
              'ELECTRODOMESTICO', 'OTRO'.
        prioridad: Urgency level. Valid: 'ALTA', 'MEDIA', 'BAJA'. Defaults to 'MEDIA'.
        costo_estimado: Estimated cost in COP. Defaults to 0.

    Returns:
        dict with 'status', 'reparacion_id', and 'responsable' per Ley 820.
    """
    rows = read_sheet("reparaciones")
    rep_id = _next_rep_id(rows)
    tipo_upper = tipo.upper()
    responsable = _RESPONSABLE.get(tipo_upper, "PROPIETARIO")

    row = {
        "reparacion_id": rep_id,
        "apt_id": apt_id,
        "contrato_id": "",
        "fecha_reporte": datetime.date.today().isoformat(),
        "descripcion": descripcion,
        "tipo": tipo_upper,
        "responsable": responsable,
        "prioridad": prioridad.upper(),
        "estado": "PENDIENTE",
        "fecha_atencion": "",
        "costo_estimado": costo_estimado if costo_estimado else "",
        "costo_real": "",
        "notas": "",
    }
    append_row("reparaciones", row)
    return {"status": "ok", "reparacion_id": rep_id, "responsable": responsable}


def resolve_repair(
    reparacion_id: str,
    costo_real: float = 0.0,
    fecha_atencion: str = "",
    notas: str = "",
) -> dict:
    """
    Marks a repair as COMPLETADO and records the final cost.

    Args:
        reparacion_id: The repair identifier, e.g. 'REP-001'.
        costo_real: Final cost in COP. Defaults to 0.
        fecha_atencion: Completion date in YYYY-MM-DD. Defaults to today.
        notas: Optional notes.

    Returns:
        dict with 'status' and confirmation message.
    """
    updates: dict = {
        "estado": "COMPLETADO",
        "fecha_atencion": fecha_atencion or datetime.date.today().isoformat(),
    }
    if costo_real:
        updates["costo_real"] = costo_real
    if notas:
        updates["notas"] = notas
    updated = update_row("reparaciones", "reparacion_id", reparacion_id, updates)
    if not updated:
        return {"status": "not_found", "message": f"Reparación {reparacion_id} no encontrada."}
    return {"status": "ok", "message": f"Reparación {reparacion_id} marcada como COMPLETADO."}


def get_repair_cost_summary(apt_id: str = "", year: int = 0) -> dict:
    """
    Returns total repair costs for completed repairs, filtered by apartment and/or year.

    Args:
        apt_id: Filter to a specific apartment. Empty means all.
        year: Filter to a specific year. Defaults to current year.

    Returns:
        dict with 'status', 'total_cop', breakdown by apartment and tipo.
    """
    if year == 0:
        year = datetime.date.today().year

    rows = read_sheet("reparaciones")
    filtered = [
        r for r in rows
        if str(r.get("estado", "")).upper() == "COMPLETADO"
        and str(r.get("fecha_reporte", "")).startswith(str(year))
    ]
    if apt_id:
        filtered = [r for r in filtered if str(r.get("apt_id", "")) == apt_id]

    total = 0.0
    by_apt: dict[str, float] = {}
    by_tipo: dict[str, float] = {}
    for r in filtered:
        costo = float(r.get("costo_real", 0) or 0)
        apt = str(r.get("apt_id", ""))
        tipo = str(r.get("tipo", "OTRO"))
        total += costo
        by_apt[apt] = by_apt.get(apt, 0.0) + costo
        by_tipo[tipo] = by_tipo.get(tipo, 0.0) + costo

    return {"status": "ok", "year": year, "total_cop": total, "por_apartamento": by_apt, "por_tipo": by_tipo}
