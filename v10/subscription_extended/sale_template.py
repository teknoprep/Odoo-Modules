
from odoo import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class sale_order_line_template(models.Model):
    _name = "sale.order.line.template"
    _description = "Template Sale Order"

    @api.multi
    def _amount_line(self):
        res = {}
        subtotal = 0.0
        for line in self.browse(self.ids):
            subtotal = line.price_unit * line.product_uom_qty
            res[line.id] = subtotal
        return res

    order_temp_id = fields.Many2one('sale.order.template','Sale Order template')
    product_id =  fields.Many2one('product.product', 'Product', required=True)
    name = fields.Char('Description', size=50)
    product_uom_qty = fields.Float('Quantity', digits= dp.get_precision('Product UoS'), required=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure ', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits= dp.get_precision('Product Price'))
    tax_id = fields.Many2many('account.tax', 'order_template_tax', 'order_line_id', 'tax_id', 'Taxes',)
    discount = fields.Float('Discount (%)', digits= dp.get_precision('Discount'))
    price_subtotal = fields.Float(compute=_amount_line, string='Subtotal', digits= dp.get_precision('Account'))

    _defaults = {
                    'product_uom_qty': 1,
    }

    @api.onchange('product_id')
    def product_id_change(self):
        res = {}

        if self.product_id:
           product = self.env['product.product'].browse(self.product_id.id)
           res = {'name' : product.name, 'product_uom': product.uom_id.id, 'price_unit': product.list_price}
           if self.order_temp_id and self.order_temp_id.invoice_type and self.order_temp_id.invoice_type == 'in_invoice':
               res['price_unit'] = product.standard_price,
               res['product_uom'] = product.uom_po_id.id
        return {'value': res}

sale_order_line_template()

class sale_order_template(models.Model):
    _name = "sale.order.template"
    _description = "Template Sale Order Line"


    name = fields.Char('Template Reference', size=64, required=True, default="/")
    sub_doc_id = fields.Many2one('subscription.subscription', size=30)
    subcription_doc_id = fields.Many2one('subscription.document', 'Subscription Doc', required=True, ondelete="cascade", size=128)
    sale_order_line = fields.One2many('sale.order.line.template', 'order_temp_id', 'Order Lines')
    date_order = fields.Date('Date', required=True, default=fields.Date.context_today)
    recurring_record = fields.Boolean('Recurring')
    model_name = fields.Char('Model Name', size=64)
    partner_id = fields.Many2one('res.partner', 'Customer')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=False, help="Pricelist for current sales order.")
    invoice_type = fields.Selection([('out_invoice','Customer Invoice'),('in_invoice','Supplier Invoice')], 'Invoice Type', size=40)
    company_id = fields.Many2one('res.company', 'Company')

    @api.onchange('subcription_doc_id')
    def onchange_sub_doc(self):
        ret_val = {'value': {'model_name': ''}}
        if self.subcription_doc_id:
            ret_val['value']['model_name'] = self.env['subscription.document'].browse(self.subcription_doc_id.id).model.model
        return ret_val

    @api.onchange('pricelist_id', 'sale_order_line')
    def onchange_pricelist_id(self):
        if not self.pricelist_id:
            return {}
        value = {
            'currency_id': self.env['product.pricelist'].browse(self.pricelist_id.id).currency_id.id
        }
        if not order_lines or order_lines == [(6, 0, [])]:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning, 'value': value}

    @api.multi
    def write(self, vals):
        so_tmplt_brw = self.browse(self.ids)
        subscription_obj = self.env['subscription.subscription']
        search_ids = subscription_obj.search([('template_order_id','=', self.ids[0])])
        for_line_ids = []
        if search_ids :
            subscription = subscription_obj.browse(search_ids.id)
            for_line_ids.append(subscription.template_ids1.id)
        for_line_ids = list(set(for_line_ids))
        so_line_tmpl_obj = self.pool.get('sale.order.line.template')

        related_so_line_tmpls = self.browse(for_line_ids)

        updated = super(sale_order_template, self).write(vals)
        for related_so_line in related_so_line_tmpls:
            related_so_line.sale_order_line.unlink()

        new_line_vals = []
        for line_id in self.browse().sale_order_line:
            current_line = so_line_tmpl_obj.read(cr,uid,line_id)
            new_line_val = {}
            new_line_val['discount'] = current_line['discount']
            new_line_val['order_temp_id'] = False
            new_line_val['name'] = current_line['name']
            new_line_val['product_id'] = current_line['product_id'][0]
            new_line_val['product_uom'] = current_line['product_uom'][0]
            new_line_val['product_uom_qty'] = current_line['product_uom_qty']
            new_line_val['price_unit'] = current_line['price_unit']
            new_line_val['tax_id'] = current_line['tax_id']
            new_line_vals.append(new_line_val)

        for other_line_id in for_line_ids:
            for line_val in new_line_vals:
                line_val['order_temp_id'] = other_line_id
                so_line_tmpl_obj.create(line_val)

        subscription_state = subscription_obj.browse(search_ids.id).state

        res = subscription_obj.browse(search_ids.id).cron_id
        res = subscription_obj.read(['cron_id'])
        ids2 = [x['cron_id'][0] for x in res if x['id']]

        res = subscription_obj.browse(search_ids.id)
        cron_ids2 = [x.cron_id for x in res if x.id]

        for cron in cron_ids2:
            cron.write({'active':False, 'doall': False})

        data = subscription_obj.browse(search_ids.id)
        print "\n sale_order_template=> write()-> data",data
        for row in data:
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
            for key,value in mapping.items():
                res[value] = row[key]
            if res and res.has_key('nextcall'):
                nextcall = self.env['ir.cron'].browse([cron.id for cron in cron_ids2])
                res['nextcall'] = nextcall.nextcall
            cron_id = self.env['ir.cron'].create(res)
            row.write({'cron_id':cron_id.id, 'state':'running'})

        return updated

    @api.model
    def create(self, vals):
        if vals.get('name','/')=='/':
            vals['name'] = self.env['ir.sequence'].get('sale.order.template') or '/'
        return super(sale_order_template, self).create(vals)

sale_order_template()
