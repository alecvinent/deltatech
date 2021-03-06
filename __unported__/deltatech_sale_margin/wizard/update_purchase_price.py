# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



from odoo import models, fields, api


class commission_update_purchase_price(models.TransientModel):
    _name = 'commission.update.purchase.price'
    _description = "Update purchase price"

    for_all = fields.Boolean(string="For all lines")
    price_from_doc = fields.Boolean(string="Price from delivery", default=True)

    invoice_line_ids = fields.Many2many('sale.margin.report', 'commission_update_purchase_price_inv_rel', 'compute_id',
                                        'invoice_line_id',
                                        string='Account invoice line')

    @api.model
    def default_get(self, fields):
        defaults = super(commission_update_purchase_price, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)

        if active_ids:
            domain = [('id', 'in', active_ids)]
        else:
            domain = [('state', '=', 'paid'), ('commission', '=', 0.0)]
        res = self.env['sale.margin.report'].search(domain)
        defaults['invoice_line_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.multi
    def do_compute(self):
        res = []
        if self.for_all:
            lines = self.env['sale.margin.report'].search([])
        else:
            lines = self.invoice_line_ids

        for line in lines:
            invoice_line = self.env['account.invoice.line'].browse(line.id)
            purchase_price = 0.0
            pickings = self.env['stock.picking']
            if self.price_from_doc:
                for sale_line in invoice_line.sale_line_ids:
                    pickings |= sale_line.order_id.picking_ids

            moves = self.env['stock.move'].search([('picking_id', 'in', pickings.ids),
                                                   ('product_id', '=', invoice_line.product_id.id)])

            qty = 0.0
            amount = 0.0
            for move in moves:
                for quant in move.quant_ids:
                    amount = amount + quant.inventory_value
                    qty = qty + quant.qty
                if qty > 0:
                    purchase_price = amount / qty

            else:
                if invoice_line.product_id:
                    if invoice_line.product_id.standard_price > 0:
                        purchase_price = invoice_line.product_id.standard_price

            if purchase_price:
                invoice_line.write({'purchase_price': purchase_price})
        return True
