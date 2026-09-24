frappe.ui.form.on("Class Session", {
    setup(frm) {
        frm.set_query("trainer", function () {
            return {
                filters: {
                    status: "Active",
                    specialization: frm.doc.session_type
                }
            };
        });
    },
    trainer(frm) {
        if (frm.doc.trainer) {
            frm.dashboard.add_comment(
                `Selected trainer: ${frm.doc.trainer}`,
                "blue",
                true
            );
        }
    },

    refresh(frm) {
        if (frm.doc.status) {
            let indicator_color = "blue";

            if (frm.doc.status === "Scheduled") {
                indicator_color = "orange";
            } else if (frm.doc.status === "Completed") {
                indicator_color = "green";
            } else if (frm.doc.status === "Cancelled") {
                indicator_color = "red";
            } else if (frm.doc.status === "Draft") {
                indicator_color = "blue";
            }

            frm.dashboard.add_indicator(
                frm.doc.status,
                indicator_color
            );
        }
        if (
            frm.doc.status === "Scheduled" &&
            frm.doc.session_date &&
            frappe.datetime.get_diff(
                frappe.datetime.get_today(),
                frm.doc.session_date
            ) >= 0
        ) {
            frm.add_custom_button("Finalize Session", function () {
                frm.set_value("status", "Completed");
                frm.save();
            });
        }
       
        if (!frm.is_new() && frm.doc.docstatus !== 2) {
            frm.add_custom_button("Cancel Session", () => {
                const dialog = new frappe.ui.Dialog({
                    title: "Cancel Session",
                    fields: [
                        {
                            label: "Cancellation Reason",
                            fieldname: "reason",
                            fieldtype: "Small Text",
                            reqd: 1
                        }
                    ],
                    primary_action_label: "Confirm Cancellation",
                    primary_action: async (values) => {
                        await frappe.call({
                            method: "flexledger.api.cancel_class_session",
                            args: {
                                session_name: frm.doc.name,
                                  reason: values.reason
                            }
                        });

                        dialog.hide();
                        await frm.reload_doc();
                    }
                });

                dialog.show();
            });
        }

        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button("Swap Trainer", () => {
                frappe.prompt(
                    [
                        {
                            label: "New Trainer",
                            fieldname: "trainer",
                            fieldtype: "Link",
                            options: "Trainer",
                            reqd: 1,
                            get_query: () => ({
                                filters: {
                                    status: "Active",
                                    specialization: frm.doc.session_type
                                }
                            })
                        }
                    ],
                    (values) => {
                        frappe.confirm(
                            `Swap the trainer to ${values.trainer}?`,
                            async () => {
                                await frappe.call({
                                    method: "flexledger.api.swap_class_trainer",
                                    args: {
                                        session_name: frm.doc.name,
                                        trainer: values.trainer
                                    }
                                });

                                await frm.reload_doc();
                                frm.trigger("trainer");
                            }
                        );
                    },
                    "Swap Trainer",
                    "Continue"
                );
            });
        }
    }
});

frappe.ui.form.on("Attendee Entry", {
    async member(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        await frappe.model.set_value(cdt, cdn, {
            package_purchase: "",
            remaining_credits: 0
        });

        if (!row.member || !frm.doc.session_type) {
            if (row.member && !frm.doc.session_type) {
                frappe.msgprint(
                    "Please select a Session Type first."
                );
            }
            return;
        }
        const response = await frappe.call({
            method: "flexledger.api.get_member_active_package_balance",
            args: {
                member: row.member
            }
        });
        if (locals[cdt]?.[cdn]?.member !== row.member) {
            return;
        }
        const package_data = response.message;
        if (!package_data) {
            frappe.msgprint(
                `No eligible active package found for ${row.member}.`
            );
            return;
        }
        await frappe.model.set_value(cdt, cdn, {
            package_purchase: package_data.name,
            remaining_credits: package_data.credits_remaining
        });
        const required = await frappe.db.get_value(
            "Session Type",
            frm.doc.session_type,
            "credits_required"
        );
        const credits_required = required.message.credits_required;
        if (package_data.credits_remaining < credits_required) {
            frappe.msgprint({
                title: "Insufficient Credits",
                indicator: "orange",
                message:
                    `${row.member} has only ` +
                    `${package_data.credits_remaining} credits. ` +
                    `This session requires ${credits_required} credits.`
            });
        }

        frm.refresh_field("attendees");
    }
});
