import frappe
from frappe.query_builder import DocType

@frappe.whitelist()
def get_low_balance_members():

    threshold = frappe.db.get_single_value("Studio Settings", "low_balance_alert_threshold")

    if threshold is None:
        threshold = 2

    PP = DocType("Package Purchase")

    result = (
        frappe.qb.from_(PP)
        .select(PP.name, PP.member, PP.credits_remaining, PP.expiry_date)
        .where(PP.credits_remaining <= threshold) & (PP.status == "Active")
        .orderby(PP.credits_remaining.asc())
        .run(as_dict=True)
    )
    return result