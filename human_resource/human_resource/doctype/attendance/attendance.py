# Copyright (c) 2023, Zak and contributors
# For license information, please see license.txt
from datetime import datetime

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class Attendance(Document):


	def on_submit(self):
		self.check_both_checks()
		self.set_work_late_hours()
		self.update_status()

	def update_status(self):
		att_settings = get_attendance_settings()
		threshold_absent = att_settings.working_hours_threshold_for_absent
		if threshold_absent:
			if self.work_hours <= threshold_absent:
				self.status = 'Absent'

	def set_work_late_hours(self):

		att_settings = get_attendance_settings()
		start_time = att_settings.start_time
		end_time = att_settings.end_time
		late_entry = att_settings.late_entry_grace_period
		early_exit = att_settings.early_exit_grace_period

		work_hours = time_diff_in_hours(self.check_out, self.check_in)
		user_late_entry = time_diff_in_hours(self.check_in, start_time)
		user_early_exit = time_diff_in_hours(end_time, self.check_out)
		user_late_hours = user_late_entry + user_early_exit

		hours_out = self.get_hours_out()
		work_hours -= hours_out
		user_late_hours += hours_out

		if not late_entry and not early_exit:
			self.work_hours = work_hours
			self.late_hours = user_late_hours
			return

		extra_hours = 0
		if late_entry and user_late_entry > 0:
			late_entry = late_entry / 60  # convert minutes to hours
			if user_late_entry <= late_entry:
				extra_hours += user_late_entry
			else:
				extra_hours += late_entry

		if early_exit and user_early_exit > 0:
			early_exit = early_exit / 60  # convert minutes to hours

			if user_early_exit <= early_exit:
				extra_hours += user_early_exit
			else:
				extra_hours += early_exit

		self.work_hours = work_hours + extra_hours
		self.late_hours = user_late_hours - extra_hours

	def get_hours_out(self):
		att_settings = get_attendance_settings()
		start_time = att_settings.start_time
		end_time = att_settings.end_time
		hours_out = 0
		hours_out_before = time_diff_in_hours(start_time, self.check_in)
		hours_out_after = time_diff_in_hours(self.check_out, end_time)
		if hours_out_before > 0:
			hours_out += hours_out_before
		if hours_out_after > 0 :
			hours_out += hours_out_after

		return hours_out

	def check_both_checks(self):
		if not (self.check_in and self.check_out):
			frappe.throw("You have to choose (check_in) and (check_out)")

		diff_checks = time_diff_in_hours(self.check_out, self.check_in)
		if diff_checks <= 0:
			frappe.throw("(check_in) Can NOT be After (check_out)")


def time_diff(datetime2, datetime1, as_minutes=False) -> float:
	if isinstance(datetime1, str):
		datetime1 = convert_to_datetime(datetime1)

	if isinstance(datetime2, str):
		datetime2 = convert_to_datetime(datetime2)

	time_diffr = datetime2 - datetime1
	if as_minutes:
		time_diffr = time_diffr.total_seconds() / 60
	else:
		time_diffr = time_diffr.total_seconds() / 3600
	return time_diffr


def convert_to_datetime(my_str):
	my_time = datetime.strptime(my_str, "%H:%M:%S")
	return my_time


def get_attendance_settings():
	att_settings = frappe.get_doc('Attendance Settings')
	return att_settings

########################################################################################################################
# token 10e98ac9063722c:8ad636d248e886b
#


@frappe.whitelist()
def create_attendance(attendance_date, check_in, check_out):
	employee = frappe.db.exists("Employee", {"user": frappe.session.user})
	if not employee:
		prepare_response(404, "faild", "User not Linked to Employee")
		return

	att = frappe.new_doc("Attendance")
	att.attendance_date = attendance_date
	att.check_in = check_in
	att.check_out = check_out
	att.employee = employee
	att.insert(ignore_permissions=True)
	att.reload()
	frappe.db.commit()
	return att


def prepare_response(status_code, _type, message, data=None):
	if data is None:
		data = dict()

	frappe.local.response["http_status_code"] = status_code
	frappe.local.response["api_status"] = {
		"type": _type,
		"message": message,
	}
	frappe.local.response["data"] = data
