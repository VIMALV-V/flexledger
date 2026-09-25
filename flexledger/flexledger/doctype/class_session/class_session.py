
import frappe
from frappe.model.document import Document

class ClassSession(Document):

    def validate(self):
        if (
            self.status == "Draft"
            and self.session_date
            and frappe.utils.getdate(self.session_date)
            < frappe.utils.getdate(frappe.utils.today())
        ):
            frappe.throw(
                "Session date cannot be in the past for a Draft session."
            )
        credits_required = frappe.db.get_value(
            "Session Type",
            self.session_type,
            "credits_required"
        )
        for row in self.attendees:
            package_member = frappe.db.get_value(
                "Package Purchase",
                row.package_purchase,
                "member"
            )
            if package_member != row.member:
                frappe.throw(
                    f"Package Purchase {row.package_purchase} is not for {row.member}"
                )
            package = frappe.db.get_value(
                "Package Purchase",
                row.package_purchase,
                ["status", "expiry_date", "credits_remaining"],
                as_dict=True
            )
            if not package:
                frappe.throw(
                    f"Package Purchase {row.package_purchase} does not exist."
                )
            if package.status != "Active":
                frappe.throw(
                    f"Package {row.package_purchase} for member {row.member} is not active. "
                )
            if (
                package.expiry_date
                and self.session_date
                and frappe.utils.getdate(package.expiry_date)
                < frappe.utils.getdate(self.session_date)
            ):
                frappe.throw(
                    f"Package {row.package_purchase} for member {row.member} has expired"
                )
            row.credits_charged = credits_required
            if package.credits_remaining < row.credits_charged:
                frappe.throw(
                    f"Member {row.member} has only {package.credits_remaining} credits remaining, but {row.credits_charged} credits are required."
                )
    def before_submit(self):
        if self.status != "Completed":
            frappe.throw(
                "Class Session can be submitted only when status is Completed."
            )
        for row in self.attendees:
            if row.attendance_status == "Booked":
                frappe.throw(
                    f"Attendance for member {row.member} is still Booked."
                )
    def on_submit(self):
        settings = frappe.get_single("Studio Settings")
        for row in self.attendees:
            charge_credit = False

            if row.attendance_status == "Attended":
                charge_credit = True
            elif (
                row.attendance_status == "No-Show"
                and settings.no_show_forfeits_credit
            ):
                charge_credit = True
            if not charge_credit:
                continue
            package = frappe.db.get_value(
                "Package Purchase",
                row.package_purchase,
                ["credits_used", "credits_remaining", "status"],
                as_dict=True
            )
            new_credits_used = (
                package.credits_used + row.credits_charged
            )
            new_credits_remaining = (
                package.credits_remaining - row.credits_charged
            )
            frappe.db.set_value(
                "Package Purchase",
                row.package_purchase,
                {
                    "credits_used": new_credits_used,
                    "credits_remaining": new_credits_remaining
                },
                update_modified=False
            )
            if new_credits_remaining == 0:
                frappe.db.set_value(
                    "Package Purchase",
                    row.package_purchase,
                    "status",
                    "Fully Used",
                    update_modified=False
                )
            threshold = settings.low_balance_alert_threshold
            if new_credits_remaining <= threshold:
                frappe.enqueue(
                    "flexledger.api.send_low_balance_email",
                    package_purchase=row.package_purchase,
                    member=row.member
                )
    

    def on_cancel(self):
        for row in self.attendees:
            charged = (
                row.attendance_status == "Attended"
                or (
                    row.attendance_status == "No-Show"
                    and frappe.get_single(
                        "Studio Settings"
                    ).no_show_forfeits_credit
                )
            )
            if not charged:
                continue
            package = frappe.db.get_value(
                "Package Purchase",
                row.package_purchase,
                ["credits_used", "credits_remaining", "status"],
                as_dict=True
            )
            new_credits_used =package.credits_used - row.credits_charged
            new_credits_remaining =package.credits_remaining + row.credits_charged
            frappe.db.set_value(
                "Package Purchase",
                row.package_purchase,
                {
                    "credits_used": new_credits_used,
                    "credits_remaining": new_credits_remaining
                },
                update_modified=False
            )
            if package.status == "Fully Used":
                frappe.db.set_value(
                    "Package Purchase",
                    row.package_purchase,
                    "status",
                    "Active",
                    update_modified=False
                )
        self.db_set("status", "Cancelled")

    def on_trash(self):
        if self.status not in ("Draft", "Cancelled"):
            frappe.throw(
                "Class Session can only be deleted when it is "
                "Draft or Cancelled."
            )

    def on_update(self):

        pass


