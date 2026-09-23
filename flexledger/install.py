import frappe


def after_install():
    create_default_session_types()
    create_default_studio_settings()

    frappe.msgprint(
        "FlexLedger installed successfully. "
        "Default Session Types and Studio Settings have been created."
    )


def create_default_session_types():
    session_types = [
        {
            "session_type_name": "1:1 Personal Training",
            "credits_required": 2,
        },
        {
            "session_type_name": "Group HIIT",
            "credits_required": 1,
        },
        {
            "session_type_name": "Yoga Flow",
            "credits_required": 1,
        },
    ]

    for data in session_types:
        if not frappe.db.exists(
            "Session Type",
            {"session_type_name": data["session_type_name"]},
        ):
            frappe.get_doc(
                {
                    "doctype": "Session Type",
                    "session_type_name": data["session_type_name"],
                    "credits_required": data["credits_required"],
                }
            ).insert(ignore_permissions=True)


def create_default_studio_settings():
    if not frappe.db.exists("Studio Settings", "Studio Settings"):
        frappe.get_doc(
            {
                "doctype": "Studio Settings",
                "studio_name": "FlexLedger Studio",
            }
        ).insert(ignore_permissions=True)
