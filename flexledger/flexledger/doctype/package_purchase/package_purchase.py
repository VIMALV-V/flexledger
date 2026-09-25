# Copyright (c) 2026, Vimal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PackagePurchase(Document):

    def before_print(self, print_settings=None):
        self.print_summary = (
            f"{self.member} - {self.total_credits} credits"
        )