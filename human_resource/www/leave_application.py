import frappe

def get_context(context):
    context['leave_applications'] = get_leave_applications()


def get_leave_applications():
    return frappe.db.sql(''' select employee_name, leave_type, total_leave_days from `tabLeave Application` ''', as_dict=1)
