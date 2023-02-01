# Copyright (c) 2023, Zak and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Max, Min
from frappe.utils import (
	date_diff,
	getdate,
)

from frappe.model.document import Document


class LeaveApplication(Document):

	def validate(self):
		self.validate_dates()
		self.set_total_leave_days()
		self.set_leave_balance_before_application()
		self.check_leave_balance()

	def on_submit(self):
		self.update_leave_balance()

	def set_total_leave_days(self):
		if self.from_date and self.to_date:
			from_date = getdate(self.from_date)
			to_date = getdate(self.to_date)
			diff_days = date_diff(to_date, from_date) + 1
			if self.total_leave_days <= 0:
				frappe.throw(f'(To Date) Should be Greater than (From Date),diff_days = {diff_days} !!! ')

			self.total_leave_days = diff_days

	def update_leave_balance(self):
		allocation_doc = frappe.get_last_doc('Leave Allocation', filters={'employee': self.employee,
						'from_date': ['<=', self.from_date],
						'to_date': ['>=', self.to_date],
						'leave_type': self.leave_type
						})

		allocation_doc.total_leaves_allocated -= self.total_leave_days
		allocation_doc.save()

	def validate_dates(self):
		if self.from_date and self.to_date and (getdate(self.to_date) < getdate(self.from_date)):
			frappe.throw("To date cannot be before from date")

	def set_leave_balance_before_application(self):
		if self.from_date and self.to_date:
			allocations = get_leave_allocation_records(self.employee, self.from_date, self.to_date, self.leave_type)
			if not allocations:
				frappe.throw(f'This Employee does NOT have any leave allocations in this period (for this Leave Type)!')

			allocation = allocations.get(self.leave_type)
			self.leave_balance_before_application = allocation.get('total_leaves_allocated')

	def check_leave_balance(self):
		if self.total_leave_days and self.leave_balance_before_application:
			if self.total_leave_days > self.leave_balance_before_application:
				frappe.throw('You do Not have enough balance')


def get_leave_allocation_records(employee, from_date, to_date, leave_type=None):
	"""Returns the total allocated leaves"""
	allocation_doc = frappe.qb.DocType("Leave Allocation")

	query = (
		frappe.qb.from_(allocation_doc)
		.select(
			Min(allocation_doc.from_date).as_("from_date"),
			Max(allocation_doc.to_date).as_("to_date"),
			allocation_doc.leave_type,
			allocation_doc.total_leaves_allocated,
		)
		.where(
			(allocation_doc.from_date <= from_date)
			& (allocation_doc.to_date >= to_date)
			& (allocation_doc.employee == employee)
		)
	)

	if leave_type:
		query = query.where((allocation_doc.leave_type == leave_type))
	query = query.groupby(allocation_doc.employee, allocation_doc.leave_type)

	allocation_details = query.run(as_dict=True)

	allocated_leaves = frappe._dict()
	for d in allocation_details:
		allocated_leaves.setdefault(
			d.leave_type,
			frappe._dict(
				{
					"from_date": d.from_date,
					"to_date": d.to_date,
					"leave_type": d.leave_type,
					"total_leaves_allocated": d.total_leaves_allocated,
				}
			),
		)

	return allocated_leaves
