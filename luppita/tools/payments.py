"""Tools for tracking rent payments and tenant payment status."""

import datetime

from ..sheets import append_row, find_rows, generate_id, get_config_value, read_sheet


def _current_period() -> str:
    today = datetime.date.today()
    return f"{today.year}-{today.month:02d}"


def _nombre_completo(inq: dict) -> str:
    return f"{inq.get('nombre', '')} {inq.get('apellido', '')}".strip()


def _get_inquilino(inquilino_id: str, inquilinos: list[dict]) -> dict:
    return next((i for i in inquilinos if str(i.get("inquilino_id", "")) == inquilino_id), {})


def get_unpaid_this_month() -> dict:
    """
    Returns all apartments whose rent has not been registered as paid for the
    current calendar month. Flags contracts with no payment row as SIN_REGISTRO.

    Returns:
        dict with 'status', 'periodo' (YYYY-MM), 'count', and 'pendientes'.
    """
    periodo = _current_period()
    contratos = read_sheet("contratos")
    pagos = read_sheet("pagos")
    inquilinos = read_sheet("inquilinos")

    paid_aptos = {
        str(p.get("apt_id"))
        for p in pagos
        if str(p.get("periodo")) == periodo
        and str(p.get("estado")).upper() in ("PAGADO", "PARCIAL")
    }

    pendientes = []
    for c in contratos:
        if str(c.get("estado", "")).upper() != "VIGENTE":
            continue
        apt = str(c.get("apt_id", ""))
        if apt not in paid_aptos:
            inq = _get_inquilino(str(c.get("inquilino_id", "")), inquilinos)
            has_row = any(
                str(p.get("apt_id")) == apt and str(p.get("periodo")) == periodo
                for p in pagos
            )
            pendientes.append({
                "apt_id": apt,
                "nombre_inquilino": _nombre_completo(inq),
                "canon_mensual": c.get("canon_mensual", 0),
                "situacion": "PENDIENTE" if has_row else "SIN_REGISTRO",
            })

    return {"status": "ok", "periodo": periodo, "count": len(pendientes), "pendientes": pendientes}


def get_payment_history(apt_id: str, meses: int = 6) -> dict:
    """
    Returns the payment history for a specific apartment over the last N months.

    Args:
        apt_id: The apartment identifier, e.g. 'APT-001'.
        meses: Number of past months to include. Defaults to 6.

    Returns:
        dict with 'status' and 'pagos' sorted by periodo desc.
    """
    today = datetime.date.today()
    oldest_month = today.month - meses
    oldest_year = today.year
    while oldest_month <= 0:
        oldest_month += 12
        oldest_year -= 1
    oldest_period = f"{oldest_year}-{oldest_month:02d}"

    pagos = read_sheet("pagos")
    history = [
        p for p in pagos
        if str(p.get("apt_id")) == apt_id
        and str(p.get("periodo", "")) >= oldest_period
    ]
    history.sort(key=lambda p: p.get("periodo", ""), reverse=True)
    return {"status": "ok", "apt_id": apt_id, "count": len(history), "pagos": history}


def get_tenants_in_arrears() -> dict:
    """
    Returns tenants with one or more months in PENDIENTE or VENCIDO state.

    Returns:
        dict with 'status', 'count', and 'morosos'.
    """
    pagos = read_sheet("pagos")
    contratos = read_sheet("contratos")
    inquilinos = read_sheet("inquilinos")
    active_contracts = {
        str(c.get("apt_id")): c
        for c in contratos
        if str(c.get("estado", "")).upper() == "VIGENTE"
    }

    arrears: dict[str, dict] = {}
    for p in pagos:
        apt = str(p.get("apt_id", ""))
        if str(p.get("estado", "")).upper() not in ("PENDIENTE", "VENCIDO"):
            continue
        if apt not in active_contracts:
            continue
        if apt not in arrears:
            contrato = active_contracts[apt]
            inq = _get_inquilino(str(contrato.get("inquilino_id", "")), inquilinos)
            arrears[apt] = {
                "apt_id": apt,
                "nombre_inquilino": _nombre_completo(inq),
                "telefono": inq.get("telefono", ""),
                "meses_mora": 0,
                "total_adeudado": 0.0,
                "periodos": [],
            }
        arrears[apt]["meses_mora"] += 1
        arrears[apt]["total_adeudado"] += (
            float(p.get("monto_esperado", 0)) - float(p.get("monto_pagado", 0))
        )
        arrears[apt]["periodos"].append(p.get("periodo", ""))

    morosos = sorted(arrears.values(), key=lambda x: x["meses_mora"], reverse=True)
    return {"status": "ok", "count": len(morosos), "morosos": morosos}


def register_payment(
    apt_id: str,
    periodo: str,
    monto_pagado: float,
    fecha_pago: str,
    metodo_pago: str = "transferencia",
    fecha_vencimiento: str = "",
    comprobante: str = "",
) -> dict:
    """
    Registers a rent payment received for a specific apartment and billing period.

    Args:
        apt_id: The apartment identifier, e.g. 'APT-001'.
        periodo: Billing period in YYYY-MM format, e.g. '2026-04'.
        monto_pagado: Amount received in COP.
        fecha_pago: Date payment was received in YYYY-MM-DD format.
        metodo_pago: Payment method: 'transferencia', 'efectivo', 'cheque'.
        fecha_vencimiento: Due date in YYYY-MM-DD. If blank, defaults to last day of periodo.
        comprobante: Bank reference or receipt number. Optional.

    Returns:
        dict with 'status', 'pago_id', and payment details.
    """
    contratos = find_rows("contratos", {"apt_id": apt_id, "estado": "VIGENTE"})
    if not contratos:
        return {"status": "error", "message": f"No se encontró contrato vigente para {apt_id}."}
    contrato = contratos[0]
    monto_esperado = float(contrato.get("canon_mensual", 0))

    if not fecha_vencimiento:
        year, month = periodo.split("-")
        fecha_vencimiento = f"{year}-{month}-01"

    if monto_pagado >= monto_esperado:
        estado = "PAGADO"
    elif monto_pagado > 0:
        estado = "PARCIAL"
    else:
        estado = "PENDIENTE"

    pago_id = generate_id("PAG", "pagos", "pago_id")
    row = {
        "pago_id": pago_id,
        "contrato_id": contrato.get("contrato_id", ""),
        "apt_id": apt_id,
        "inquilino_id": contrato.get("inquilino_id", ""),
        "periodo": periodo,
        "fecha_vencimiento": fecha_vencimiento,
        "fecha_pago": fecha_pago,
        "monto_esperado": monto_esperado,
        "monto_pagado": monto_pagado,
        "estado": estado,
        "metodo_pago": metodo_pago,
        "comprobante": comprobante,
        "notas": "",
    }
    append_row("pagos", row)
    return {
        "status": "ok",
        "pago_id": pago_id,
        "monto_esperado": monto_esperado,
        "monto_pagado": monto_pagado,
        "diferencia": monto_pagado - monto_esperado,
        "estado_pago": estado,
    }


def get_monthly_income_summary(periodo: str = "") -> dict:
    """
    Returns expected vs received rent income for a given month.

    Args:
        periodo: Billing period in YYYY-MM format. Defaults to current month.

    Returns:
        dict with 'status', 'periodo', totals, and per-apartment breakdown.
    """
    if not periodo:
        periodo = _current_period()

    contratos = read_sheet("contratos")
    pagos = read_sheet("pagos")
    inquilinos = read_sheet("inquilinos")
    active = {
        str(c.get("apt_id")): c
        for c in contratos
        if str(c.get("estado", "")).upper() == "VIGENTE"
    }
    pagos_periodo = {str(p.get("apt_id")): p for p in pagos if str(p.get("periodo")) == periodo}

    breakdown = []
    total_esperado = 0.0
    total_recibido = 0.0

    for apt, contrato in active.items():
        esperado = float(contrato.get("canon_mensual", 0))
        pago = pagos_periodo.get(apt)
        recibido = float(pago.get("monto_pagado", 0)) if pago else 0.0
        estado = pago.get("estado", "SIN_REGISTRO") if pago else "SIN_REGISTRO"
        inq = _get_inquilino(str(contrato.get("inquilino_id", "")), inquilinos)
        total_esperado += esperado
        total_recibido += recibido
        breakdown.append({
            "apt_id": apt,
            "inquilino": _nombre_completo(inq),
            "monto_esperado": esperado,
            "monto_recibido": recibido,
            "diferencia": recibido - esperado,
            "estado": estado,
        })

    return {
        "status": "ok",
        "periodo": periodo,
        "total_esperado": total_esperado,
        "total_recibido": total_recibido,
        "diferencia": total_recibido - total_esperado,
        "breakdown": breakdown,
    }


def calculate_rent_increase(apt_id: str, ipc_pct: float = 0.0) -> dict:
    """
    Calculates the new canon after the annual IPC-based rent increase.

    Args:
        apt_id: The apartment identifier.
        ipc_pct: IPC percentage to apply. If 0, reads ipc_anio_anterior from config.

    Returns:
        dict with canon_actual, ipc_aplicado, canon_nuevo, and differences.
    """
    if ipc_pct == 0.0:
        raw = get_config_value("ipc_anio_anterior")
        try:
            ipc_pct = float(raw)
        except (TypeError, ValueError):
            return {"status": "error", "message": "No se encontró 'ipc_anio_anterior' en config."}

    contratos = find_rows("contratos", {"apt_id": apt_id, "estado": "VIGENTE"})
    if not contratos:
        return {"status": "not_found", "message": f"No se encontró contrato vigente para {apt_id}."}
    contrato = contratos[0]
    inquilinos = read_sheet("inquilinos")
    inq = _get_inquilino(str(contrato.get("inquilino_id", "")), inquilinos)
    canon_actual = float(contrato.get("canon_mensual", 0))
    canon_nuevo = round(canon_actual * (1 + ipc_pct / 100))
    return {
        "status": "ok",
        "apt_id": apt_id,
        "inquilino": _nombre_completo(inq),
        "canon_actual": canon_actual,
        "ipc_aplicado": ipc_pct,
        "canon_nuevo": canon_nuevo,
        "diferencia_mensual": canon_nuevo - canon_actual,
        "diferencia_anual": (canon_nuevo - canon_actual) * 12,
    }
