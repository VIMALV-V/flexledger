
import frappe


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = [
        {
            "label": "Trainer",
            "fieldname": "trainer",
            "fieldtype": "Link",
            "options": "Trainer",
        },
        {
            "label": "Sessions Run",
            "fieldname": "sessions_run",
            "fieldtype": "Int"
        },
        {
            "label": "Total Attendees",
            "fieldname": "total_attendees",
            "fieldtype": "Int"
        },
        {
            "label": "No-Show Rate %",
            "fieldname": "no_show_rate",
            "fieldtype": "Percent"
        },
        {
            "label": "Credits Processed",
            "fieldname": "credits_processed",
            "fieldtype": "Int"
        }
    ]
    conditions = {"docstatus": 1}

    if filters.get("from_date"):
        conditions["session_date"] = [">=", filters.from_date]

    if filters.get("to_date"):
        if filters.get("from_date"):
            conditions["session_date"] = [
                "between",
                [filters.from_date, filters.to_date]
            ]
        else:
            conditions["session_date"] = ["<=", filters.to_date]

    if filters.get("trainer"):
        conditions["trainer"] = filters.trainer

    sessions = frappe.get_list(
        "Class Session",
        filters=conditions,
        fields=["name", "trainer"],
        page_length=0
    )
    data = []

    for session in sessions:
        if not session.trainer:
            continue
        attendees = frappe.get_all(
            "Attendee Entry",
            filters={"parent": session.name},
            fields=["attendance_status", "credits_charged"]
        )
        row = next(
            (r for r in data if r["trainer"] == session.trainer),
            None
        )

        if not row:
            row = {
                "trainer": session.trainer,
                "sessions_run": 0,
                "total_attendees": 0,
                "no_shows": 0,
                "credits_processed": 0
            }
            data.append(row)
        row["sessions_run"] += 1

        for attendee in attendees:
            if attendee.attendance_status == "Cancelled":
                continue
            row["total_attendees"] += 1

            if attendee.attendance_status == "No-Show":
                row["no_shows"] += 1

            row["credits_processed"] += attendee.credits_charged or 0

    for row in data:
        if row["total_attendees"]:
            row["no_show_rate"] = round(
                row["no_shows"] / row["total_attendees"] * 100,
                2
            )
        else:
            row["no_show_rate"] = 0
    return columns, data
