# Copyright (c) 2026, Vimal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PackagePurchase(Document):

    def autoname(self):
        member_name = frappe.db.get_value(
            "Member",
            self.member,
            "member_name"
        )
        if not member_name:
            frappe.throw("Member is required to generate Package Purchase name.")
        words = member_name.strip().split()

        if len(words) == 1:
            short_code = words[0][:2].upper()
        else:
            short_code = "".join(word[0] for word in words).upper()

        prefix = f"{short_code}-"
        last_package = frappe.db.sql(
            """
            SELECT name
            FROM `tabPackage Purchase`
            WHERE name LIKE %s
            ORDER BY name DESC
            LIMIT 1
            """,
            (prefix + "%",),
            as_dict=True
        )
        if last_package:
            last_number = int(last_package[0].name.split("-")[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        self.name = f"{prefix}{next_number:04d}"
