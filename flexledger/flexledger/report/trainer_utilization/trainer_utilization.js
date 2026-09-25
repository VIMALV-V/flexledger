
frappe.query_reports["Trainer Utilization"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_end()
        },
        {
            fieldname: "trainer",
            label: __("Trainer"),
            fieldtype: "Link",
            options: "Trainer"
        }
    ],
    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "no_show_rate" && data) {
            if (data.no_show_rate > 25) {
                value = `<span style="color:red">${value}</span>`;
            } else if (data.no_show_rate < 10) {
                value = `<span style="color:green">${value}</span>`;
            }
        }
        return value;
    }
};