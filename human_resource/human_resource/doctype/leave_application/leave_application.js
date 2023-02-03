// Copyright (c) 2023, Zak and contributors
// For license information, please see license.txt

 frappe.ui.form.on("Leave Application", {
// 	refresh(frm) {
//
// 	},

    employee: function(frm){
    frm.trigger("get_total_leaves");
    },
    leave_type: function(frm){
    frm.trigger("get_total_leaves");
    },
    from_date: function(frm){
    frm.trigger("get_total_leaves");
    frm.trigger("get_diff_days");
    },
    to_date: function(frm){
    frm.trigger("get_total_leaves");
    frm.trigger("get_diff_days");
    },

    get_total_leaves: function(frm){
    if(! (frm.doc.employee && frm.doc.leave_type && frm.doc.from_date && frm.doc.to_date)){
        return;
    }

    frappe.call({
    method:"human_resource.human_resource.doctype.leave_application.leave_application.get_leave_allocation_records",
    args: {
        employee:frm.doc.employee,
        leave_type:frm.doc.leave_type,
        from_date:frm.doc.from_date,
        to_date:frm.doc.to_date
    },
    callback: (r)=>{
    frm.doc.leave_balance_before_application=r.message.total_leaves_allocated;
    frm.refresh();

    }

    })
    },

    get_diff_days: function(frm){
    if(! (frm.doc.from_date && frm.doc.to_date)){
        return;
    }

    frappe.call({
    method:"human_resource.human_resource.doctype.leave_application.leave_application.get_total_leave_days",
    args: {
        from_date:frm.doc.from_date,
        to_date:frm.doc.to_date
    },
    callback: (r)=>{
    frm.doc.total_leave_days=r.message;
    frm.refresh();

    }

    })
    }

 });

