// Copyright (c) 2023, Zak and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee", {
// 	refresh(frm) {

// 	},
// });

// employee - validate date_of_birth
frappe.ui.form.on('Employee', {
 validate(frm) {
if (frm.doc.date_of_birth >= get_today()  ) {
 frappe.throw('You can not select date of birth after today');
}
} })


// employee - validate count_employee_education
frappe.ui.form.on('Employee',  { validate: function(frm) {
 var total_education = 0;
 $.each(frm.doc.education,  function(i,  d) {
 if ( d.school_university){
 total_education += 1; }
 });
frm.doc.count_employee_education = total_education;
}
 });
