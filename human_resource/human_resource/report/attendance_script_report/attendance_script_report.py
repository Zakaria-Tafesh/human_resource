# Copyright (c) 2023, Zak and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from typing import Dict, List

Filters = frappe._dict


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data()

	return columns, data


def get_columns() -> List[Dict]:
	return [

		{
			"label": _("Employee"),
			"fieldtype": "Link",
			"fieldname": "employee",
			"width": 150,
			"options": "Employee",
		},
		{
			"label": _("Employee Name"),
			"fieldtype": "Dynamic Link",
			"fieldname": "employee_name",
			"width": 150,
			"options": "employee",
		},
		{
			"label": _("Attendance Date"),
			"fieldtype": "Data",
			"fieldname": "attendance_date",
			"width": 150,
		},
		{
			"label": _("Department"),
			"fieldtype": "Link",
			"fieldname": "department",
			"width": 100,
			"options": "Department",
		},
		{
			"label": _("Status"),
			"fieldtype": "Data",
			"fieldname": "status",
			"width": 150,
		},
		{
			"label": _("Check In"),
			"fieldtype": "Data",
			"fieldname": "check_in",
			"width": 150,
		},
		{
			"label": _("Check  Out"),
			"fieldtype": "Data",
			"fieldname": "check_out",
			"width": 150,
		},
		{
			"label": _("Work Hours"),
			"fieldtype": "float",
			"fieldname": "work_hours",
			"width": 150,
		},
		{
			"label": _("Late Hours"),
			"fieldtype": "float",
			"fieldname": "late_hours",
			"width": 150,
		},

	]


def get_data():
	data = []
	attendance = frappe.db.get_list('Attendance', fields=['employee', 'employee_name', 'attendance_date',
														'department', 'status', 'check_in', 'check_out', 'work_hours',
														'late_hours'])

	# for att in attendance:

	# data = [
	# 	{
	# 		'employee': 'Zakaria Tafesh',
	# 		'employee_name': 'Zak Omer Tafesh',
	# 	},
	#
	#
	# ]

	return attendance
