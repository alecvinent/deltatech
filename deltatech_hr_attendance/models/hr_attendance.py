# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
import pytz
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

def utc_to_local(event_time):
    tz_name = "Europe/Bucharest"
    tz = pytz.timezone(tz_name)

    event_time = pytz.UTC.localize(event_time).astimezone(tz).replace(tzinfo=None)

    return event_time




class hr_attendance(models.Model):
    _inherit = "hr.attendance"

    for_date = fields.Date(string='For Date', compute="_compute_for_date", store=True, readonly=False)

    state = fields.Selection([('ok','OK'),('no_in','No check in'),('no_out','No check out'),('manual','Manual')], default='ok')
    # salvez departamentul din momentul in care a fost facut pontajul
    department_id = fields.Many2one('hr.department', string='Department',   compute="_compute_department", store=True, readonly=False)


    @api.multi
    @api.depends('employee_id')
    def _compute_department(self):
        for attendance in self:
            attendance.department_id =  attendance.employee_id.department_id

    @api.multi
    def action_add_day(self):
        for_date = fields.Date.from_string(self.for_date)
        for_date = for_date + relativedelta(days=1)
        self.for_date =fields.Date.to_string(for_date)
        line = self.env['hr.attendance.sheet.line'].search( [('date', '=',  self.for_date),
                                                             ('employee_id', '=', self.employee_id.id)])
        line.action_invalidate()

    @api.multi
    def action_minus_day(self):
        for_date = fields.Date.from_string(self.for_date)
        for_date = for_date + relativedelta(days=-1)
        self.for_date = fields.Date.to_string(for_date)
        line = self.env['hr.attendance.sheet.line'].search([('date', '=', self.for_date),
                                                            ('employee_id', '=', self.employee_id.id)])
        line.action_invalidate()




    @api.multi
    @api.depends('check_in', 'check_out')
    def _compute_for_date(self):
        day_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_start', 6)
        day_start = int(day_start)
        # caclul ora de inceput zi lucratoare
        for attendance in self:
            if attendance.check_in:
                if attendance.employee_id.shift in ['F','T']:
                    day_start = 0
                date_time_in = fields.Datetime.from_string(attendance.check_in) - timedelta(hours=day_start)
                date_time_in = utc_to_local(date_time_in)
                date_in = fields.Date.to_string(date_time_in)
                attendance.for_date = date_in
                if attendance.check_out:
                    date_time_out = fields.Datetime.from_string(attendance.check_out) - timedelta(hours=day_start)
                    date_time_out = utc_to_local(date_time_out)
                    date_out = fields.Date.to_string(date_time_out)
                    if date_in != date_out:
                        date_time_00 = fields.Datetime.from_string(date_out + ' 00:00:00')
                        d1 = date_time_00 - date_time_in
                        d2 = date_time_out - date_time_00
                        if d2 > d1:
                            attendance.for_date = date_out


