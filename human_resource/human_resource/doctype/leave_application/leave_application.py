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
	def get_feed(self):
		return _("{0}: From {0} of type {1}").format(self.employee_name, self.leave_type)

	def validate(self):
		self.validate_dates()
		self.validate_balance_leaves()

	def on_submit(self):
		allocation_doc = frappe.get_last_doc('Leave Allocation', filters={'employee': self.employee,
						'from_date': ['<=', self.from_date],
						'to_date': ['>=', self.to_date],
						'leave_type': self.leave_type
						})

		allocation_doc.total_leaves_allocated -= self.total_leave_days
		allocation_doc.save()


	def validate_dates(self):
		# if frappe.db.get_single_value("HR Settings", "restrict_backdated_leave_application"):
		if self.from_date and getdate(self.from_date) < getdate():
			frappe.throw(_("(From Date) Can NOT be before today, You have to choose a date After {}").format(
				frappe.bold(self.from_date)))


		if self.from_date and self.to_date and (getdate(self.to_date) < getdate(self.from_date)):
			frappe.throw(_("To date cannot be before from date"))

	def validate_balance_leaves(self):

		if self.from_date and self.to_date:
			from_date = getdate(self.from_date)
			to_date = getdate(self.to_date)
			diff_days = date_diff(to_date, from_date)
			# diff = relativedelta.relativedelta(to_date, from_date)
			# diff_days = float(diff.days)
			self.total_leave_days = diff_days
			if self.total_leave_days <= 0:
				frappe.throw(
					_(
						f'(To Date) Should be Greater than (From Date),diff_days = {diff_days} !!! '
					)
				)

			allocations = get_leave_allocation_records(self.employee, self.from_date, self.to_date, self.leave_type)
			if not allocations:
				frappe.throw(
					_(
						f'This Employee does NOT have any leave allocations in this period (for this Leave Type)! '
					)
				)

			allocation = allocations.get(self.leave_type)

			self.leave_balance_before_application = allocation.get('total_leaves_allocated')

			if self.total_leave_days > self.leave_balance_before_application:
				frappe.throw(
					_(
						f'You do Not have enough balance'
					)
				)


def get_leave_allocation_records(employee, from_date, to_date, leave_type=None):
	"""Returns the total allocated leaves"""
	Allocation = frappe.qb.DocType("Leave Allocation")

	query = (
		frappe.qb.from_(Allocation)
		.select(
			Min(Allocation.from_date).as_("from_date"),
			Max(Allocation.to_date).as_("to_date"),
			Allocation.leave_type,
			Allocation.total_leaves_allocated,
		)
		.where(
			(Allocation.from_date <= from_date)
			& (Allocation.to_date >= to_date)
			& (Allocation.employee == employee)
		)
	)

	if leave_type:
		query = query.where((Allocation.leave_type == leave_type))
	query = query.groupby(Allocation.employee, Allocation.leave_type)

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
