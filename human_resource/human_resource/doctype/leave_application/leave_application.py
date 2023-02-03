# Copyright (c) 2023, Zak and contributors
# For license information, please see license.txt
from datetime import datetime # from python std library
import frappe
from frappe import _
from frappe.query_builder.functions import Max, Min
from frappe.utils import (
	date_diff,
	getdate,
	add_to_date
)

from frappe.model.document import Document


class LeaveApplication(Document):

	def validate(self):
		self.validate_dates()
		self.validate_applicable_after()
		self.set_total_leave_days()
		self.set_leave_balance_before_application()
		self.check_leave_balance()
		self.validate_max_continuous_days()

	def on_submit(self):
		self.update_leave_balance_decrease()

	def on_cancel(self):
		self.update_leave_balance_increase()

	def validate_max_continuous_days(self):
		max_cont_allowed = self.get_max_cont_days()
		if self.total_leave_days and max_cont_allowed:
			if self.total_leave_days > max_cont_allowed:
				frappe.throw(f'This period is too long, max_cont_allowed={max_cont_allowed}')

	def validate_applicable_after(self):
		self.validate_both_dates_exists()
		applicable_after = self.get_applicable_after()
		if applicable_after:  # So will ignore if the value = 0
			after_days = add_to_date(datetime.now(), days=applicable_after, as_string=True)  # today + applicable_after
			if date_diff(getdate(self.from_date), getdate(after_days)) < 0:
				frappe.throw(f'You have to apply for this leave type at least after {applicable_after} days from now')

	def get_max_cont_days(self):
		leave_type_doc = frappe.get_last_doc('Leave Type', filters={'leave_type_name': self.leave_type})
		if leave_type_doc:
			max_cont_days = leave_type_doc.max_continuous_days_allowed
			return max_cont_days

	def set_total_leave_days(self):
		self.validate_both_dates_exists()

		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date)
		diff_days = date_diff(to_date, from_date) + 1
		if diff_days <= 0:
			frappe.throw(f'(To Date) Should be Greater than (From Date),diff_days = {diff_days} !!! ')

		self.total_leave_days = diff_days

	def update_leave_balance_decrease(self):
		allocation_doc = self.get_same_leave_allocation_doc()
		allocation_doc.total_leaves_allocated -= self.total_leave_days
		allocation_doc.save()

	def update_leave_balance_increase(self):
		allocation_doc = self.get_same_leave_allocation_doc()
		allocation_doc.total_leaves_allocated += self.total_leave_days
		allocation_doc.save()

	def get_same_leave_allocation_doc(self):
		allocation_doc = frappe.get_last_doc('Leave Allocation', filters={'employee': self.employee,
						'from_date': ['<=', self.from_date],
						'to_date': ['>=', self.to_date],
						'leave_type': self.leave_type
						})
		return allocation_doc

	def validate_dates(self):
		self.validate_both_dates_exists()
		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw("To date cannot be before from date")

	def validate_both_dates_exists(self):
		if not (self.from_date and self.to_date):
			frappe.throw("You have to choose (from date) and (to date)")

	def set_leave_balance_before_application(self):
		if self.from_date and self.to_date:
			allocations = get_leave_allocation_records(self.employee, self.from_date, self.to_date, self.leave_type)
			if not allocations:
				frappe.throw(f'This Employee does NOT have any leave allocations in this period (for this Leave Type)!')

			allocation = allocations.get(self.leave_type)
			self.leave_balance_before_application = allocation.get('total_leaves_allocated')

	def check_leave_balance(self):
		allow_negative_balance = self.get_allow_negative_balance()
		if allow_negative_balance:
			return
		if self.total_leave_days and self.leave_balance_before_application:
			if self.total_leave_days > self.leave_balance_before_application:
				frappe.throw('You do Not have enough balance')

	def get_allow_negative_balance(self):
		allow_negative_balance = frappe.get_value('Leave Type', self.leave_type, 'allow_negative_balance')
		return allow_negative_balance

	def get_applicable_after(self):
		applicable_after = frappe.get_value('Leave Type', self.leave_type, 'applicable_after')
		return applicable_after

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
