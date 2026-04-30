from .alerts import get_apartment_status, get_full_dashboard
from .contracts import (
    add_contract,
    get_all_contracts,
    get_contract_by_apartment,
    get_expiring_contracts,
    get_tenant_info,
    update_contract_status,
)
from .maintenance import (
    get_pending_repairs,
    get_repair_cost_summary,
    log_repair,
    resolve_repair,
)
from .payments import (
    calculate_rent_increase,
    get_monthly_income_summary,
    get_payment_history,
    get_tenants_in_arrears,
    get_unpaid_this_month,
    register_payment,
)
from .taxes import (
    add_tax_record,
    get_predial_info,
    get_tax_calendar,
    get_upcoming_tax_deadlines,
    mark_tax_paid,
)

ALL_TOOLS = [
    # Contracts
    get_all_contracts,
    get_expiring_contracts,
    get_contract_by_apartment,
    get_tenant_info,
    add_contract,
    update_contract_status,
    # Payments
    get_unpaid_this_month,
    get_payment_history,
    get_tenants_in_arrears,
    register_payment,
    get_monthly_income_summary,
    calculate_rent_increase,
    # Repairs
    get_pending_repairs,
    log_repair,
    resolve_repair,
    get_repair_cost_summary,
    # Taxes
    get_upcoming_tax_deadlines,
    get_tax_calendar,
    mark_tax_paid,
    get_predial_info,
    add_tax_record,
    # Dashboard
    get_full_dashboard,
    get_apartment_status,
]
