import frappe
from frappe.query_builder import DocType

@frappe.whitelist()
def get_low_balance_members():
    threshold = frappe.db.get_single_value(
        "Studio Settings",
        "low_balance_alert_threshold"
    )
    pp = DocType("Package Purchase")
    result = (
        frappe.qb
        .from_(pp)
        .select(
            pp.name,
            pp.member,
            pp.credits_remaining,
            pp.expiry_date
        )
        .where(
            (pp.credits_remaining <= threshold)
            & (pp.status == "Active")
        )
        .orderby(pp.credits_remaining)
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
    frappe.share.add(
        "Class Session",
        session_name,
        user,
        read=1
    )

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
            f"Your package {package_purchase} has only {credits_remaining} credits remaining."
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

@frappe.whitelist()
def get_member_active_package_balance(member):
    packages = frappe.get_list(
        "Package Purchase",
        filters={
            "member": member,
            "status": "Active",
            "credits_remaining": [">", 0],
            "expiry_date": [">=", frappe.utils.today()]
        },
        fields=["name", "credits_remaining"],
        order_by="expiry_date asc",
        limit_page_length=1
    )

    return packages[0] if packages else None

@frappe.whitelist()
def cancel_class_session(session_name, reason):
    if not reason or not reason.strip():
        frappe.throw("Cancellation Reason is required.")

    session = frappe.get_doc("Class Session", session_name)
    session.check_permission("write")

    if session.docstatus == 2:
        frappe.throw("This session is already cancelled.")

    if session.docstatus == 1:
        session.check_permission("cancel")
        session.db_set("cancellation_reason", reason.strip())
        session.cancel()
    else:
        session.status = "Cancelled"
        session.cancellation_reason = reason.strip()
        session.save()

    return {"message": "Session cancelled successfully"}


@frappe.whitelist()
def swap_class_trainer(session_name, trainer):
    session = frappe.get_doc("Class Session", session_name)
    session.check_permission("write")

    if session.docstatus != 0:
        frappe.throw("Only draft sessions can have their trainer changed.")

    trainer_doc = frappe.get_doc("Trainer", trainer)

    if trainer_doc.status != "Active":
        frappe.throw("The selected trainer is not Active.")

    if trainer_doc.specialization != session.session_type:
        frappe.throw("Trainer specialization does not match the session type.")

    session.trainer = trainer
    session.save()

    return {"message": "Trainer changed successfully"}