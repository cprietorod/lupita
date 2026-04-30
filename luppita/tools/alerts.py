"""Dashboard and alert tools that aggregate data across all domains."""

import datetime

from ..sheets import read_sheet
from .contracts import get_expiring_contracts
from .maintenance import get_pending_repairs
from .payments import get_tenants_in_arrears, get_unpaid_this_month
from .taxes import get_upcoming_tax_deadlines


def _nombre_completo(inq: dict) -> str:
    return f"{inq.get('nombre', '')} {inq.get('apellido', '')}".strip()


def get_full_dashboard() -> dict:
    """
    Returns a comprehensive summary of all active alerts across the portfolio:
    unpaid rents, expiring contracts, pending repairs, and upcoming tax deadlines.

    Returns:
        dict with 'status', 'resumen', and sections for each domain.
    """
    unpaid = get_unpaid_this_month()
    expiring = get_expiring_contracts(days_ahead=90)
    pending_repairs = get_pending_repairs()
    tax_deadlines = get_upcoming_tax_deadlines(days_ahead=60)
    arrears = get_tenants_in_arrears()

    urgent_repairs = [r for r in pending_repairs.get("pendientes", []) if r.get("urgente")]

    return {
        "status": "ok",
        "resumen": {
            "aptos_sin_pago_este_mes": unpaid.get("count", 0),
            "contratos_por_vencer_90_dias": expiring.get("count", 0),
            "reparaciones_pendientes": pending_repairs.get("count", 0),
            "reparaciones_urgentes": len(urgent_repairs),
            "arrendatarios_en_mora": arrears.get("count", 0),
            "impuestos_proximos_60_dias": tax_deadlines.get("count", 0),
        },
        "pagos_pendientes": unpaid.get("pendientes", []),
        "arrendatarios_en_mora": arrears.get("morosos", []),
        "contratos_por_vencer": expiring.get("contratos", []),
        "reparaciones_urgentes": urgent_repairs,
        "impuestos_proximos": tax_deadlines.get("eventos", []),
    }


def get_apartment_status(apt_id: str) -> dict:
    """
    Returns the complete current status for a single apartment: info, active contract,
    last payment, open repairs, and next tax deadline.

    Args:
        apt_id: The apartment identifier, e.g. 'APT-001'.

    Returns:
        dict with 'status', semaforo indicator, and all relevant data.
    """
    today = datetime.date.today()
    periodo_actual = f"{today.year}-{today.month:02d}"

    aptos = read_sheet("apartamentos")
    apto_info = next((a for a in aptos if str(a.get("apt_id", "")) == apt_id), None)
    if not apto_info:
        return {"status": "not_found", "message": f"Apartamento {apt_id} no encontrado."}

    contratos = read_sheet("contratos")
    inquilinos = read_sheet("inquilinos")
    contrato = next(
        (c for c in contratos
         if str(c.get("apt_id", "")) == apt_id
         and str(c.get("estado", "")).upper() == "VIGENTE"),
        None,
    )
    nombre_inquilino = ""
    if contrato:
        inq_id = str(contrato.get("inquilino_id", ""))
        inq = next((i for i in inquilinos if str(i.get("inquilino_id", "")) == inq_id), {})
        nombre_inquilino = _nombre_completo(inq)

    pagos = read_sheet("pagos")
    pago_mes = next(
        (p for p in pagos
         if str(p.get("apt_id", "")) == apt_id
         and str(p.get("periodo", "")) == periodo_actual),
        None,
    )

    repairs = get_pending_repairs(apt_id=apt_id)
    urgent_repairs = [r for r in repairs.get("pendientes", []) if r.get("urgente")]

    impuestos = read_sheet("impuestos")
    apt_taxes = sorted(
        [i for i in impuestos
         if str(i.get("apt_id", "")) == apt_id
         and str(i.get("estado", "")).upper() != "PAGADO"],
        key=lambda i: str(i.get("fecha_vencimiento", "")),
    )
    proximo_impuesto = apt_taxes[0] if apt_taxes else None

    semaforo = "OK"
    try:
        contrato_vencido = (
            contrato
            and str(contrato.get("fecha_fin", ""))
            and datetime.date.fromisoformat(str(contrato.get("fecha_fin"))) < today
        )
        impuesto_vencido = (
            proximo_impuesto
            and datetime.date.fromisoformat(str(proximo_impuesto.get("fecha_vencimiento", "9999-12-31"))) < today
        )
        if contrato_vencido or impuesto_vencido or urgent_repairs or (pago_mes and str(pago_mes.get("estado", "")).upper() == "VENCIDO"):
            semaforo = "CRITICO"
        elif (
            repairs.get("count", 0) > 0
            or not pago_mes
            or (contrato and str(contrato.get("fecha_fin", "")) and
                (datetime.date.fromisoformat(str(contrato.get("fecha_fin"))) - today).days <= 90)
            or (proximo_impuesto and
                (datetime.date.fromisoformat(str(proximo_impuesto.get("fecha_vencimiento", "9999-12-31"))) - today).days <= 30)
        ):
            semaforo = "ALERTA"
    except (ValueError, TypeError):
        semaforo = "ALERTA"

    return {
        "status": "ok",
        "semaforo": semaforo,
        "apartamento": apto_info,
        "inquilino": nombre_inquilino,
        "contrato_activo": contrato,
        "pago_mes_actual": pago_mes,
        "reparaciones_pendientes": repairs.get("count", 0),
        "reparaciones_urgentes": len(urgent_repairs),
        "proximo_impuesto": proximo_impuesto,
    }
