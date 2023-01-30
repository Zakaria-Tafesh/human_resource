# Copyright (c) 2023, Zak and contributors
# For license information, please see license.txt
import frappe
from dateutil import relativedelta
from frappe.model.document import Document
from frappe.utils import getdate


class Employee(Document):
	MAX_AGE = 60
	MOBILE_LEN = 10
	MOBILE_PRE = '059'
	def validate(self):
		self.validate_age_active()
		self.create_full_name()
		self.create_cv_valuation()
		self.validate_mobile()

	def after_insert(self):
		self.add_todo()

	def validate_mobile(self):
		if self.mobile:
			if not self.mobile.startswith(self.MOBILE_PRE):
				frappe.throw(f'Mobile Number should Starts with: ({self.MOBILE_PRE})')

			if len(self.mobile) != self.MOBILE_LEN:
				frappe.throw(f'Mobile length = {len(self.mobile)} !!! It should be = {self.MOBILE_LEN}')

	def add_todo(self):
		if self.first_name:
			frappe.msgprint('New employee added to ToDo')
			frappe.get_doc(dict(doctype='ToDo', status="Open",
								description="new employee " + str(self.first_name))).insert()
		else:
			frappe.msgprint('No employee added to ToDo')

	def create_cv_valuation(self):
		if self.cv:
			if 'english' in self.cv.lower():
				self.cv_valuation = 'Good'
			else:
				self.cv_valuation = 'Not Good'

	def create_full_name(self):
		names = []
		if self.first_name:
			names.append(self.first_name)
		if self.mid_name:
			names.append(self.mid_name)
		if self.last_name:
			names.append(self.last_name)

		self.full_name = ' '.join(names)

	def validate_age_active(self):
		emp_age = self.get_age()
		status = self.status.lower()

		if emp_age >= self.MAX_AGE and status == 'active':
			frappe.throw(f'This is too Old employee to be Active!!\nAge: {emp_age} -- Status: {status}')

	def get_age(self):
		age_str = ""
		age_int = 0
		if self.date_of_birth:
			born = getdate(self.date_of_birth)
			age = relativedelta.relativedelta(getdate(), born)
			age_str = str(age.years) + " year(s) " + str(age.months) + " month(s) " + str(age.days) + " day(s)"
			age_int = int(age.years)

		return age_int
