import frappe


def get_studio_name():
    return frappe.db.get_single_value(
        "Studio Settings",
        "studio_name"
    ) 
