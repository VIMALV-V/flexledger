
import frappe
from frappe.utils import today, add_days, now

def check_expiring_packages():
    already_run = frappe.db.exists(
        "Audit Log",
        {
            "action": "expiry_check",
            "timestamp": [
                "between",
                [
                    f"{today()} 00:00:00",
                    f"{today()} 23:59:59"
                ]
            ]
        }
    )
    if already_run:
        return
    packages = frappe.get_all(
        "Package Purchase",
        filters={
            "status": "Active",
            "expiry_date": [
                "between",
                [today(), add_days(today(), 7)]
            ]
        },
        fields=["name", "member", "expiry_date"]
    )
    for package in packages:
        frappe.logger("flexledger").info(
            f"Expiring package: {package.name}, "
            f"Member: {package.member}, "
            f"Expiry: {package.expiry_date}"
        )
    frappe.get_doc({
        "doctype": "Audit Log",
        "doctype_name": "Package Purchase",
        "document_name": "Daily Expiry Check",
        "action": "expiry_check",
        "user": "Administrator",
        "timestamp": now()
    }).insert(ignore_permissions=True)
