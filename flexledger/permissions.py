import frappe


def class_session_query(user):

    if not user:
        user = frappe.session.user

    if "FIT Studio Manager" in frappe.get_roles(user):
        return ""

    if "FIT Trainer" in frappe.get_roles(user):

        trainer = frappe.db.get_value(
            "Trainer",
            {"user": user},
            "name"
        )

        if not trainer:
            return "1=0"

        return f"`tabClass Session`.trainer = {frappe.db.escape(trainer)}"

    return "1=0"
