# -*- coding: utf-8 -*-

# from openerp.osv import fields,osv
from odoo import models, fields, api
from openerp.tools.translate import _
from openerp import netsvc


from datetime import datetime
import time


class subscription_subscription(models.Model):
    _inherit = "subscription.subscription"

    def _get_document_types(self):
        return [('res.partner','Partner')]

    # doc_source        = fields.Reference('Source doc', required=False, selection=[('res.partner','Partner')], size=128, help="User can choose the source document on which he wants to create documents"),
    # doc_source = fields.Reference('Source doc', required=False, selection=_get_document_types, size=128, help="User can choose the source document on which he wants to create documents")
    doc_source = fields.Reference(selection=_get_document_types, string='Source doc', required=False, size=128, help="User can choose the source document on which he wants to create documents")

    source_doc_id        = fields.Many2one('subscription.document', 'Source Document', required=True)
    template_order_id        = fields.Many2one('sale.order.template', 'Sale order')
    temp_model        = fields.Char('Temp Model', size=60)
    template_ids1        = fields.One2many('sale.order.template', 'sub_doc_id', 'Sale Order Template View ')
    term_condition        = fields.Text('Term & Condition')
    doc_type        = fields.Char('Doc type', size=40)
    notify_by_mail        = fields.Boolean('Notify By Mail', help='Use notify by mail to customer/supplier after create invoice')
    valid_invoice        = fields.Boolean('Validate', help='Use to confirm Invoice after create')
    payment_term        = fields.Many2one('account.payment.term', 'Payment Terms')


    # _defaults = {
    #                 'doc_source' : 'res.partner,1'
    # }


    @api.multi
    def write(self, vals):
        print "\n subscription_subscription==> write()-> "
        updated = super(subscription_subscription, self).write(vals)
        return updated

    @api.model
    def create(self, vals):
        print "\n subscription_subscription==> create()-> "
        new_id = super(subscription_subscription, self).create(vals)
        print "\n subscription_subscription==> create()-> new_id",new_id
        print "\n subscription_subscription==> create()-> self_data.template_ids1 ",new_id.template_ids1
        print "\n subscription_subscription==> create()-> self_data.template_ids1.sub_doc_id ", new_id.template_ids1.sub_doc_id
        self_data = self.browse(new_id.id)
        print "\n subscription_subscription==> create()-> self_data.template_ids1 ", self_data.template_ids1
        print "\n subscription_subscription==> create()-> self_data.template_ids1.sub_doc_id ", self_data.template_ids1.sub_doc_id
        if self_data.template_ids1.sub_doc_id == False:
            context['from_subscription'] = self._data
            self_data.templatemplate_ids1.write({'sub_doc_id': self_data.id})
            # self.pool.get('sale.order.template').write(cr, uid, self_data.template_ids1.id,
            #                                              {'sub_doc_id': self_data.id}, context)
        return new_id

    @api.onchange('source_doc_id')
    def onchange_source_doc(self):
        print "\n subscription_subscription==> onchange_source_doc()-> "
        if self.source_doc_id:
            return {'value': {'temp_model': 'sale.order.template'}}
        return {'value': {'temp_model': ''}}

    @api.onchange('template_ids1', 'source_doc_id')
    def onchange_template_first(self):
        print "\n subscription_subscription==> onchange_template_first()-> "

        order_template = self.pool.get('sale.order.template')
        order_line = []
        order = []
        part_ids = []
        res = {}
        rec_model_name = ''
        print " subscription_subscription==> self.source_doc_id  --> ", self.source_doc_id
        print " subscription_subscription==> self.template_ids1  --> ", self.template_ids1
        if self.template_ids1:
            order_brw = order_template.browse(self.template_ids1)
            print " subscription_subscription==> order_brw  --> ", order_brw

            for order_line_obj in order_brw.sale_order_line:
                order_data = {
                    'name': order_line_obj.name,
                    'product_uom': order_line_obj.product_uom.id,
                    'price_unit': order_line_obj.price_unit,
                    'product_id': order_line_obj.product_id.id,
                    'product_uom_qty': order_line_obj.product_uom_qty,
                    'tax_id': [(6, 0, [x.id for x in order_line_obj.tax_id])],
                    'discount': order_line_obj.discount,
                    }
                order_line.append((0,0,order_data))

            data = {
                'subcription_doc_id': order_brw.subcription_doc_id.id,
                'name': order_brw.name,
                'date_order': order_brw.date_order,
                'pricelist_id': order_brw.pricelist_id.id,
                'model_name': order_brw.model_name,
                'sub_doc_id': self.ids and self.ids[0] or False,
                'invoice_type': order_brw.invoice_type,
                'sale_order_line': order_line,
                'reccurring_record':True,
                'company_id' : order_brw.company_id and order_brw.company_id.id or False
                }
            order.append((0,0,data))

            if self.source_doc_id:
                sub_doc_brw = self.env['subscription.document'].browse(self.source_doc_id.id)
                rec_model_name = sub_doc_brw.model.model

            """Here we will create domain based on invoice type"""
            print " subscription_subscription==> rec_model_name --> ", rec_model_name
            print " subscription_subscription==> order_brw.invoice_type --> ", order_brw.invoice_type
            print " subscription_subscription==> order_brw.subscription_doc_id.invoice_type --> ", order_brw.subscription_doc_id.invoice_type
            if order_brw.subscription_doc_id.invoice_type == 'in_invoice':
                part_ids = self.env['res.partner'].search([('supplier','=',True)])
                print " subscription_subscription==> part_ids as supplier --> ", part_ids
            elif order_brw.subscription_doc_id.invoice_type == 'out_invoice' or rec_model_name == 'sale.order':
                part_ids = self.env['res.partner'].search([('customer','=',True)])
                print " subscription_subscription==> part_ids as customer --> ", part_ids
            else:
                part_ids = self.env['res.partner'].search([])
                print " subscription_subscription==> part_ids else nothing  --> ", part_ids

        res['template_ids1'] = order
        so_tmpl_data = self.env['sale.order.template'].read(self.template_ids1.id)
        # return {'value': res, 'domain': {'partner_id': [('id', 'in', part_ids)]}}
        return {'value': res, 'domain': {}}

    @api.multi
    def set_done(self):
        print "\n subscription_subscription==> set_done()-> "
        res = self.read(cr,uid, ids, ['cron_id'])
        ids2 = [x['cron_id'][0] for x in res if x['id']]
        self.pool.get('ir.cron').write(cr, uid, ids2, {'active':False, 'doall': False})
        self.write(cr, uid, ids, {'state':'done'})
        return True

    @api.multi
    def set_draft(self):
        print "\n subscription_subscription==> draft()-> "
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    @api.multi
    def set_process(self):
        print "\n subscription_subscription==> set_process()-> "
        data = self.read(cr, uid, ids, context=context)
        for row in data:
            mapping = {'name':'name',
                        'interval_number':'interval_number',
                        'interval_type':'interval_type',
                        'exec_init':'numbercall',
                        'date_init':'nextcall'
                        }
            res = {'model':'subscription.subscription',
                    'args': repr([[row['id']]]),
                    'function':'model_copy',
                    'priority':1,
                    'user_id':row['user_id'] and row['user_id'][0],
                    'doall':False}
            for key,value in mapping.items():
                res[value] = row[key]

            context.update({'from_subscription':True})
            id = self.pool.get('ir.cron').create(cr, uid, res,context=context)
            self.write(cr, uid, [row['id']], {'cron_id':id, 'state':'running'})
        return True

    @api.multi
    def model_copy(self):
        print "\n subscription_subscription==> model_copy()-> "
        for row in self.read(cr, uid, ids, context=context):
            if not row.get('cron_id',False):
                continue
            cron_ids = [row['cron_id'][0]]
            remaining = self.pool.get('ir.cron').read(cr, uid, cron_ids, ['numbercall'])[0]['numbercall']
            try:
                temp_id = row['template_ids1'][0]
                partner_id = row['partner_id'][0]
                model_name_template = row['temp_model']
                source_doc_id = row['source_doc_id'][0]
                sub_doc_obj = self.pool.get('subscription.document').browse(cr, uid, source_doc_id)
                id = sub_doc_obj.model.id
                model_name = sub_doc_obj.model.model
                model = self.pool.get(model_name)
            except:
                raise osv.except_osv(_('Wrong Source Document!'), _('Please provide another source document.\nThis one does not exist!'))

            default = {'state':'draft'}
            doc_obj = self.pool.get('subscription.document')
            document_ids = doc_obj.search(cr, uid, [('model.model','=',model_name)])
            doc = doc_obj.browse(cr, uid, document_ids)[0]
            for f in doc.field_ids:
                if f.value=='date':
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

                part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
                addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
                pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
                payment_term = part.property_payment_term and part.property_payment_term.id or False
                fiscal_position = part.property_account_position and part.property_account_position.id or False
                account_id = int(part.property_account_receivable.id)
                dedicated_salesman = part.user_id and part.user_id.id or uid
                val = {
                    'partner_invoice_id': addr['invoice'],
                    'partner_shipping_id': addr['delivery'],
                    'payment_term': payment_term,
                    'fiscal_position': fiscal_position,
                    'user_id': dedicated_salesman,
                }

                ### Browse template record to get values
                print " subscription_subscription==> >>>>>>>>>>>>>>>>>>>>", model_name_template
                order_brw = self.pool.get(str(model_name_template)).browse(cr, uid, temp_id)

                ### Create Dictionary for parent record
                default.update({
                    'partner_id': partner_id,
                    'payment_term': row['payment_term'] and row['payment_term'][0],
                    })

                ### Here we have check which object should be used to create new record
                ### Based on that assign values
                if model_name == 'sale.order':
                    default.update({'partner_shipping_id': val['partner_shipping_id'],
                                    'partner_invoice_id': val['partner_invoice_id'],
                                    'pricelist_id': order_brw.pricelist_id.id,
                                    'date_order': time.strftime('%Y-%m-%d'),})

                if model_name == 'account.invoice':
                    default.update({'name': '',
#                                    'date_invoice': order_brw.date_order,
                                    'date_invoice': time.strftime('%Y-%m-%d'),
                                    'type': order_brw.invoice_type,
                                    'account_id': account_id,
                                    'comment': row['note'],
                                    'company_id': order_brw.company_id.id
                                    })
                    print " subscription_subscription==> default ",default
                    print " subscription_subscription==> order_brw.name ",order_brw.name
                    print " subscription_subscription==> order_brw.company_id.id ",order_brw.company_id.id
                    print " subscription_subscription==> order_brw.company_id.name ",order_brw.company_id.name
                    if order_brw.invoice_type == 'out_invoice':
                        journal_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', order_brw.company_id.id)], limit=1)
                        if not journal_ids:
                            raise osv.except_osv(_('Error!'),
                                _('Please define sales journal for this company: "%s" (id:%d).') % (order_brw.company_id.name, order_brw.company_id.id))
                        default.update({'journal_id': journal_ids[0],})

                    if order_brw.invoice_type == 'in_invoice':
                        journal_ids = self.pool.get('account.journal').search(cr, uid,
                            [('type', '=', 'purchase'), ('company_id', '=', order_brw.company_id.id)],
                            limit=1)
                        if not journal_ids:
                            raise osv.except_osv(_('Error!'),
                                _('Please define purchase journal for this company: "%s" (id:%d).') % (order_brw.company_id.name, order_brw.company_id.id))
                        default.update({'journal_id': journal_ids[0],})

                ### CREate parent record for SO, and invoice
                data_id = self.pool.get(str(model_name)).create(cr, uid, default)

                ### Now get values from template line to create order line (child records)
                for order_line_obj in order_brw.sale_order_line:
                    if model_name == 'sale.order':
                        order_data = {
                            'order_id': data_id,
                            'name': order_line_obj.name,
                            'product_uom': order_line_obj.product_uom.id,
                            'price_unit': order_line_obj.price_unit,
                            'product_id': order_line_obj.product_id.id,
                            'product_uom_qty': order_line_obj.product_uom_qty,
                            'tax_id': [(6, 0, [x.id for x in order_line_obj.tax_id])],
                            'discount': order_line_obj.discount,
                            }
                        self.pool.get('sale.order.line').create(cr, uid, order_data)

                    if model_name == 'account.invoice':
                        product_account_id = order_line_obj.product_id.property_account_income and order_line_obj.product_id.property_account_income.id or False
                        if not product_account_id:
                            product_account_id = order_line_obj.product_id.categ_id.property_account_income_categ.id
                        if not product_account_id:
                            raise osv.except_osv(_('Error!'),
                                    _('Please define income account for this product: "%s" (id:%d).') % \
                                        (order_line_obj.product_id.name, order_line_obj.product_id.id,))
                        order_data = {
                            'invoice_id': data_id,
                            'name': order_line_obj.name,
                            'uos_id': order_line_obj.product_uom.id,
                            'account_id': product_account_id,
                            'price_unit': order_line_obj.price_unit,
                            'product_id': order_line_obj.product_id.id,
                            'quantity': order_line_obj.product_uom_qty,
                            'invoice_line_tax_id':[(6, 0, [x.id for x in order_line_obj.tax_id])],
                            'discount': order_line_obj.discount,
                            }
                        self.pool.get('account.invoice.line').create(cr, uid, order_data)

                if model_name == 'account.invoice':
                    ### Pass signal to confirm the invoice and show in open state
                    self.pool.get('account.invoice').button_reset_taxes(cr, uid, [data_id])
                    if row['valid_invoice']:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'account.invoice', data_id, 'invoice_open', cr)

                    """ Partner notify by mail after create invoice"""
                    email_template_obj = self.pool.get('email.template')
                    if row['notify_by_mail']:
                        template = self.pool.get('ir.model.data').get_object(cr, uid, 'account', 'email_template_edi_invoice')
                        email_template_obj.write(cr,uid,[template.id],{
                                                       'email_to':part.email,
                                                       })
                        email_template_obj.send_mail(cr, uid, template.id, data_id , True, context=context)

            self.pool.get('subscription.subscription.history').create(cr, uid, {'subscription_id': row['id'], 'date':time.strftime('%Y-%m-%d %H:%M:%S'), 'document_id': model_name+','+str(data_id)})
            self.write(cr, uid, [row['id']], {'state':state})
        return True

subscription_subscription()
