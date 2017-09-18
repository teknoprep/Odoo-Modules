# -*- coding: utf-8 -*-

from openerp.osv import osv
from odoo import models, fields, api
from openerp.tools.translate import _
from openerp import netsvc
from odoo import SUPERUSER_ID


from datetime import datetime
import time


class subscription_subscription(models.Model):
    _inherit = "subscription.subscription"

    def _get_document_types(self):
        return [('account.invoice', 'Invoice')]

    doc_source = fields.Reference(selection=_get_document_types, string='Source doc', required=False, size=128, help="User can choose the source document on which he wants to create documents")

    source_doc_id = fields.Many2one('subscription.document', 'Source Document', required=True)
    template_order_id = fields.Many2one('sale.order.template', 'Sale order')
    temp_model = fields.Char('Temp Model', size=60)
    template_ids1 = fields.One2many('sale.order.template', 'sub_doc_id', 'Sale Order Template View ')
    term_condition = fields.Text('Term & Condition')
    doc_type = fields.Char('Doc type', size=40)
    notify_by_mail = fields.Boolean('Notify By Mail', help='Use notify by mail to customer/supplier after create invoice')
    valid_invoice = fields.Boolean('Validate', help='Use to confirm Invoice after create')
    payment_term = fields.Many2one('account.payment.term', 'Payment Terms')

    @api.multi
    def write(self, vals):
        updated = super(subscription_subscription, self).write(vals)
        return updated

    @api.model
    def create(self, vals):
        new_id = super(subscription_subscription, self).create(vals)
        if new_id.template_ids1.sub_doc_id == False:
            context['from_subscription'] = self._data
            new_id.templatemplate_ids1.write({'sub_doc_id': self_data.id})
        if new_id.template_order_id:
            for order_line in new_id.template_order_id.sale_order_line:
                order_data = {
                    'name': order_line.name,
                    'product_uom': order_line.product_uom.id,
                    'price_unit': order_line.price_unit,
                    'product_id': order_line.product_id.id,
                    'product_uom_qty': order_line.product_uom_qty,
                    'tax_id': [(6, 0, [x.id for x in order_line.tax_id])],
                    'discount': order_line.discount,
                    }
                new_id.template_ids1.write({'sale_order_line': [(0, 0, order_data)]})
        return new_id

    @api.onchange('source_doc_id')
    def onchange_source_doc(self):
        if self.source_doc_id:
            return {'value': {'temp_model': 'sale.order.template'}}
        return {'value': {'temp_model': ''}}


    @api.multi
    @api.onchange('template_order_id')
    def onchange_template_first(self):
        Partner = self.env['res.partner'].sudo()
        order = []
        part_ids = []
        rec_model_name = ''
        for each in self:
            print each.template_order_id
            if each.template_order_id:
                data = {
                    'subcription_doc_id': each.template_order_id.subcription_doc_id.id,
                    'name': each.template_order_id.name,
                    'date_order': each.template_order_id.date_order,
                    'pricelist_id': each.template_order_id.pricelist_id.id,
                    'model_name': each.template_order_id.model_name,
                    'sub_doc_id': each.id or False,
                    'invoice_type': each.template_order_id.invoice_type,
                    'sale_order_line': [],
                    'reccurring_record':True,
                    'company_id' : each.template_order_id.company_id and each.template_order_id.company_id.id or False
                }
                order.append((0, 0, data))

                if self.source_doc_id:
                    rec_model_name = self.source_doc_id.model.model

                """Here we will create domain based on invoice type"""
                if each.template_order_id.invoice_type == 'in_invoice':
                    part_ids = Partner.search([('supplier', '=', True)])
                elif each.template_order_id.invoice_type == 'out_invoice' or rec_model_name == 'sale.order':
                    part_ids = Partner.search([('customer', '=', True)])
                else:
                    part_ids = Partner.search([])

        self.template_ids1 = order
        return {'domain': {'partner_id': [('id', 'in', [part_id.id for part_id in part_ids])]}}


    @api.multi
    def set_done(self):
        res = self.read(['cron_id'])
        cron_ids2 = [x.cron_id for x in self if x.id]

        for cron in cron_ids2:
            cron.write({'active':False, 'doall': False})
        self.write({'state':'done'})
        return True

    @api.multi
    def set_draft(self):
        self.write({'state':'draft'})
        return True

    @api.multi
    def set_process(self):
        for row in self:
            mapping = {'name':'name',
                        'interval_number':'interval_number',
                        'interval_type':'interval_type',
                        'exec_init':'numbercall',
                        'date_init':'nextcall'
                        }
            res = {'model':'subscription.subscription',
                    'args': repr([[row.id]]),
                    'function':'model_copy',
                    'priority':1,
                    'user_id':row.user_id and row.user_id.id,
                    'doall':False}
            for key, value in mapping.items():
                res[value] = row[key]

            cron = self.env['ir.cron'].create(res)
            row.write({'cron_id':cron.id, 'state':'running'})
        return True

    @api.multi
    def model_copy(self, *kwrgs):
        doc_obj = self.env['subscription.document']
        Partner = self.env['res.partner']
        Journal = self.env['account.journal']
        SaleOrder = self.env['sale.order.line']
        Invoice = self.pool.get('account.invoice')
        InvoiceLine = self.env['account.invoice.line']
        for row in self.sudo().browse(kwrgs and kwrgs[0] and kwrgs[0][0]):
            row = row.sudo().read()[0]
            if not row.get('cron_id', False):
                continue
            cron_id = [row['cron_id'][0]]
            remaining = self.env['ir.cron'].browse([row['cron_id'][0]]).numbercall
            try:
                temp_id = row['template_order_id'][0]
                partner_id = row['partner_id'][0]
                model_name_template = row['temp_model']
                source_doc_id = row['source_doc_id'][0]
                sub_doc_obj = self.env['subscription.document'].browse(source_doc_id)
                id = sub_doc_obj.model.id
                model_name = sub_doc_obj.model.model
                model = self.env[model_name]
            except Exception, e:
                raise osv.except_osv(_('Wrong Source Document!'), _('Please provide another source document.\nThis one does not exist!'))

            default = {'state':'draft'}
            doc = doc_obj.search([('model.model', '=', model_name)], limit=1)
            for f in doc.field_ids:
                if f.value == 'date':
                    value = time.strftime('%Y-%m-%d')
                else:
                    value = False
                if f.field.name != 'recurring_record':
                    default[f.field.name] = value

            state = 'running'

            # if there was only one remaining document to generate
            # the subscription is over and we mark it as being done
            if remaining == 1:
                state = 'done'

            if model_name_template == 'sale.order.template':

                part = Partner.sudo().browse(partner_id)
                addr = part.address_get(['delivery', 'invoice', 'contact'])
                pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
                payment_term = part.property_payment_term_id and part.property_payment_term_id.id or False
                fiscal_position = part.property_account_position_id and part.property_account_position_id.id or False
                account_id = int(part.property_account_receivable_id.id)
                dedicated_salesman = part.user_id and part.user_id.id or SUPERUSER_ID
                val = {
                    'partner_invoice_id': addr['invoice'],
                    'partner_shipping_id': addr['delivery'],
                    'payment_term_id': payment_term,
                    'fiscal_position': fiscal_position,
                    'user_id': dedicated_salesman,
                }

                # Browse template record to get values
                order_brw = self.env[str(model_name_template)].sudo().browse(temp_id)
                if not order_brw.company_id:
                    order_brw.write({'company_id': self.env.user.company_id.id})

                # Create Dictionary for parent record
                default.update({
                    'partner_id': partner_id,
                    'payment_term_id': row['payment_term'] and row['payment_term'][0],
                })

                # Here we have check which object should be used to create new record
                # Based on that assign values
                if model_name == 'sale.order':
                    default.update({'partner_shipping_id': val['partner_shipping_id'],
                                    'partner_invoice_id': val['partner_invoice_id'],
                                    'pricelist_id': order_brw.pricelist_id.id,
                                    'date_order': time.strftime('%Y-%m-%d'), })

                if model_name == 'account.invoice':
                    default.update({'name': '',
#                                    'date_invoice': order_brw.date_order,
                                    'date_invoice': time.strftime('%Y-%m-%d'),
                                    'type': order_brw.invoice_type,
                                    'account_id': account_id,
                                    'comment': row['note'],
                                    'company_id': order_brw.company_id.id
                                    })
                    if order_brw.invoice_type == 'out_invoice':
                        journal_ids = Journal.sudo().search([('type', '=', 'sale'), ('company_id', '=', order_brw.company_id.id)], limit=1)
                        if not journal_ids:
                            raise osv.except_osv(_('Error!'),
                                _('Please define sales journal for this company: "%s" (id:%d).') % (order_brw.company_id.name, order_brw.company_id.id))
                        default.update({'journal_id': journal_ids.id, })

                    if order_brw.invoice_type == 'in_invoice':
                        journal_ids = Journal.sudo().search([('type', '=', 'purchase'), ('company_id', '=', order_brw.company_id.id)],
                            limit=1)
                        if not journal_ids:
                            raise osv.except_osv(_('Error!'),
                                _('Please define purchase journal for this company: "%s" (id:%d).') % (order_brw.company_id.name, order_brw.company_id.id))
                        default.update({'journal_id': journal_ids.id, })

                # CREate parent record for SO, and invoice
                data_id = self.env[str(model_name)].sudo().create(default)

                # Now get values from template line to create order line (child records)
                for order_line_obj in order_brw.sale_order_line:
                    if model_name == 'sale.order':
                        order_data = {
                            'order_id': data_id and data_id.id or False,
                            'name': order_line_obj.name,
                            'product_uom': order_line_obj.product_uom.id,
                            'price_unit': order_line_obj.price_unit,
                            'product_id': order_line_obj.product_id.id,
                            'product_uom_qty': order_line_obj.product_uom_qty,
                            'tax_id': [(6, 0, [x.id for x in order_line_obj.tax_id])],
                            'discount': order_line_obj.discount,
                            }
                        SaleOrder.sudo().create(order_data)

                    if model_name == 'account.invoice':
                        product_account_id = order_line_obj.product_id.property_account_income_id and order_line_obj.product_id.property_account_income_id.id or False
                        if not product_account_id:
                            product_account_id = order_line_obj.product_id.categ_id.property_account_income_categ_id.id
                        if not product_account_id:
                            raise osv.except_osv(_('Error!'),
                                    _('Please define income account for this product: "%s" (id:%d).') % \
                                        (order_line_obj.product_id.name, order_line_obj.product_id.id,))
                        order_data = {
                            'invoice_id': data_id and data_id.id or False,
                            'name': order_line_obj.name,
                            'uom_id': order_line_obj.product_uom.id,
                            'account_id': product_account_id,
                            'price_unit': order_line_obj.price_unit,
                            'product_id': order_line_obj.product_id.id,
                            'quantity': order_line_obj.product_uom_qty,
                            'invoice_line_tax_ids':[(6, 0, [x.id for x in order_line_obj.tax_id])],
                            'discount': order_line_obj.discount,
                            }
                        InvoiceLine.sudo().create(order_data)

                if model_name == 'account.invoice':
                    # Pass signal to confirm the invoice and show in open state
                    data_id.action_invoice_open()

#                     """ Partner notify by mail after create invoice"""
                    email_template_obj = self.env['mail.template']
                    if row['notify_by_mail']:
                        template = self.env['ir.model.data'].get_object('account', 'email_template_edi_invoice')[1]
                        email_template_obj.sudo().browse(template).write({'email_to':part.email})
                        email_template_obj.sudo().browse(template).send_mail(data_id and data_id.id or False, force_send=True)

            self.write({'state':state})
        return True
