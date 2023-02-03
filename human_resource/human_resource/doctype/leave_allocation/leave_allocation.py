# Copyright (c) 2023, Zak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class LeaveAllocation(Document):
	def validate(self):
		self.validate_dates()
		self.check_exist_already()

	def validate_dates(self):
		if self.from_date and self.to_date and (getdate(self.to_date) < getdate(self.from_date)):
			frappe.throw("To date cannot be before from date")

	def check_exist_already(self):
		allocation_doc = frappe.db.sql(''' select * from `tabLeave Allocation` where employee=%(employee)s and 
		leave_type = %(leave_type)s and ( from_date between %(from_date)s and %(to_date)s or
		to_date between %(from_date)s and %(to_date)s ) and not name = %(name)s  ''', {'employee': self.employee,
													'leave_type': self.leave_type,
													'from_date': self.from_date,
													'to_date': self.to_date,
													'name': self.name
		                                                                               })
		if allocation_doc:
			frappe.throw('This Employee already have this leave type in the same period')
		return allocation_doc
