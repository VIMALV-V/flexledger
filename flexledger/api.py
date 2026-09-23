import frappe
from frappe.query_builder import DocType


@frappe.whitelist()
def get_low_balance_members():

    threshold = frappe.db.get_single_value(
        "Studio Settings",
        "low_balance_alert_threshold"
    )

    if threshold is None:
        threshold = 2

    PP = DocType("Package Purchase")

    result = (
        frappe.qb
        .from_(PP)
        .select(
            PP.name,
            PP.member,
            PP.credits_remaining,
            PP.expiry_date
        )
        .where(
            (PP.credits_remaining <= threshold)
            & (PP.status == "Active")
        )
        .orderby(PP.credits_remaining)
        .run(as_dict=True)
    )

    return result

@frappe.whitelist()
def transfer_package(package_name, new_member):

    try:
        frappe.db.sql(
            """
            UPDATE `tabPackage Purchase`
            SET member = %s
            WHERE name = %s
            AND credits_used = 0
            """,
            (new_member, package_name)
        )

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "FlexLedger Package Transfer Failed"
        )
        raise

@frappe.whitelist()
def share_class_session(session_name, user_email):

    user = frappe.db.get_value(
        "User",
        {"email": user_email},
        "name"
    )

    if not user:
        frappe.throw("User with this email does not exist")

    frappe.share.add(
        "Class Session",
        session_name,
        user,
        read=1
    )

    return {
        "message": "Class Session shared successfully",
        "session": session_name,
        "user": user_email
    }


@frappe.whitelist()
def get_members_unsafe():

    return frappe.get_all(
        "Member",
        fields=[
            "name",
            "member_name",
            "phone",
            "email"
        ]
    )

@frappe.whitelist()
def get_members_safe():

    members = frappe.get_list(
        "Member",
        fields=[
            "name",
            "member_name",
            "phone",
            "email"
        ]
    )

    if "FIT Studio Manager" not in frappe.get_roles():

        for member in members:
            member.pop("phone", None)
            member.pop("email", None)

    return members


@frappe.whitelist()
def send_low_balance_email(package_purchase, member):
    member_email = frappe.db.get_value(
        "Member",
        member,
        "email"
    )

    if not member_email:
        return

    credits_remaining = frappe.db.get_value(
        "Package Purchase",
        package_purchase,
        "credits_remaining"
    )

    frappe.sendmail(
        recipients=[member_email],
        subject="Low Package Credit Balance",
        message=(
            f"Your package {package_purchase} has only "
            f"{credits_remaining} credits remaining."
        )
    )


@frappe.whitelist()
def rename_member(old_name, new_name):
    frappe.rename_doc(
        "Member",
        old_name,
        new_name,
        merge=False
    )

    return {
        "old_name": old_name,
        "new_name": new_name
    }