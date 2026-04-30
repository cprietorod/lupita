"""Tools for managing lease contracts and tenant information."""

import datetime

from ..sheets import append_row, find_rows, generate_id, read_sheet, update_row


def _nombre_completo(inq: dict) -> str:
    return f"{inq.get('nombre', '')} {inq.get('apellido', '')}".strip()


def _enrich_with_inquilino(row: dict, inquilinos: list[dict]) -> dict:
    inq_id = str(row.get("inquilino_id", ""))
    inq = next((i for i in inquilinos if str(i.get("inquilino_id", "")) == inq_id), {})
    row = dict(row)
    row["nombre_inquilino"] = _nombre_completo(inq)
    row["telefono_inquilino"] = inq.get("telefono", "")
    return row


def get_all_contracts(estado: str = "VIGENTE") -> dict:
    """
    Returns all lease contracts, optionally filtered by status.

    Args:
        estado: Filter by contract status. Valid values: 'VIGENTE', 'TERMINADO',
                'RENOVADO'. Use 'TODOS' to return all contracts.

    Returns:
        dict with 'status', 'count', and 'contratos' enriched with inquilino name.
    """
    rows = read_sheet("contratos")
    inquilinos = read_sheet("inquilinos")
    if estado.upper() != "TODOS":
        rows = [r for r in rows if str(r.get("estado", "")).upper() == estado.upper()]
    contratos = [_enrich_with_inquilino(r, inquilinos) for r in rows]
    return {"status": "ok", "count": len(contratos), "contratos": contratos}


def get_expiring_contracts(days_ahead: int = 90) -> dict:
    """
    Returns VIGENTE contracts expiring within the next N days.

    Args:
        days_ahead: Look-ahead window in days. Defaults to 90.

    Returns:
        dict with 'status', 'count', and 'contratos' with dias_para_vencer added.
        Contracts with blank fecha_fin (indefinite) are excluded.
    """
    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days_ahead)
    rows = read_sheet("contratos")
    inquilinos = read_sheet("inquilinos")
    expiring = []
    for row in rows:
        if str(row.get("estado", "")).upper() != "VIGENTE":
            continue
        fecha_fin_str = str(row.get("fecha_fin", ""))
        if not fecha_fin_str:
            continue
        try:
            fecha_fin = datetime.date.fromisoformat(fecha_fin_str)
        except ValueError:
            continue
        if today <= fecha_fin <= cutoff:
            row = _enrich_with_inquilino(row, inquilinos)
            row["dias_para_vencer"] = (fecha_fin - today).days
            expiring.append(row)
    expiring.sort(key=lambda r: r["fecha_fin"])
    return {"status": "ok", "count": len(expiring), "contratos": expiring}


def get_contract_by_apartment(apt_id: str) -> dict:
    """
    Returns the active (VIGENTE) lease contract for a specific apartment.

    Args:
        apt_id: The apartment identifier, e.g. 'APT-001'.

    Returns:
        dict with 'status' and 'contrato' enriched with inquilino data.
    """
    rows = find_rows("contratos", {"apt_id": apt_id, "estado": "VIGENTE"})
    if not rows:
        return {"status": "not_found", "message": f"No se encontró contrato vigente para {apt_id}."}
    inquilinos = read_sheet("inquilinos")
    return {"status": "ok", "contrato": _enrich_with_inquilino(rows[0], inquilinos)}


def get_tenant_info(nombre_inquilino: str) -> dict:
    """
    Searches for a tenant by name (first or last) and returns their info and active contract.

    Args:
        nombre_inquilino: Partial or full name (case-insensitive).

    Returns:
        dict with 'status', 'count', and 'resultados' (list of inquilino + contrato).
    """
    inquilinos = read_sheet("inquilinos")
    contratos = read_sheet("contratos")
    query = nombre_inquilino.lower()
    matches = [
        i for i in inquilinos
        if query in str(i.get("nombre", "")).lower()
        or query in str(i.get("apellido", "")).lower()
    ]
    result = []
    for inq in matches:
        inq_id = str(inq.get("inquilino_id", ""))
        contrato = next(
            (c for c in contratos
             if str(c.get("inquilino_id", "")) == inq_id
             and str(c.get("estado", "")).upper() == "VIGENTE"),
            None,
        )
        result.append({"inquilino": inq, "nombre_completo": _nombre_completo(inq), "contrato_activo": contrato})
    return {"status": "ok", "count": len(result), "resultados": result}


def add_contract(
    apt_id: str,
    inquilino_id: str,
    fecha_inicio: str,
    fecha_fin: str,
    canon_mensual: float,
    deposito: float = 0.0,
) -> dict:
    """
    Adds a new lease contract to the contratos sheet.

    Args:
        apt_id: Apartment identifier (e.g. 'APT-001').
        inquilino_id: Tenant identifier (e.g. 'INQ-001').
        fecha_inicio: Lease start date in YYYY-MM-DD format.
        fecha_fin: Lease end date in YYYY-MM-DD. Leave blank for indefinite term.
        canon_mensual: Monthly rent amount in COP.
        deposito: Security deposit in COP. Defaults to 0.

    Returns:
        dict with 'status' and 'contrato_id'.
    """
    contrato_id = generate_id("CONT", "contratos", "contrato_id")
    row = {
        "contrato_id": contrato_id,
        "apt_id": apt_id,
        "inquilino_id": inquilino_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "canon_mensual": canon_mensual,
        "deposito": deposito,
        "estado": "VIGENTE",
        "notas": "",
    }
    append_row("contratos", row)
    return {"status": "ok", "contrato_id": contrato_id}


def update_contract_status(contrato_id: str, nuevo_estado: str) -> dict:
    """
    Updates the status of an existing contract.

    Args:
        contrato_id: The contract identifier, e.g. 'CONT-2026-001'.
        nuevo_estado: New status. Valid values: 'VIGENTE', 'TERMINADO', 'RENOVADO'.

    Returns:
        dict with 'status' and confirmation message.
    """
    valid = {"VIGENTE", "TERMINADO", "RENOVADO"}
    if nuevo_estado.upper() not in valid:
        return {"status": "error", "message": f"Estado inválido. Use: {valid}"}
    updated = update_row("contratos", "contrato_id", contrato_id, {"estado": nuevo_estado.upper()})
    if not updated:
        return {"status": "not_found", "message": f"Contrato {contrato_id} no encontrado."}
    return {"status": "ok", "message": f"Contrato {contrato_id} actualizado a '{nuevo_estado.upper()}'."}
