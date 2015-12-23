
from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class sale_order_line_template(osv.osv):
    _name = "sale.order.line.template"
    _description = "Template Sale Order"


    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        subtotal = 0.0
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            subtotal = line.product_id.list_price * line.product_uom_qty
            res[line.id] = subtotal
        return res
    
    _columns = {
                    'order_temp_id'   : fields.many2one('sale.order.template','Sale Order template'),
                    'product_id'      : fields.many2one('product.product', 'Product', required=True),
                    'name'            : fields.char('Description', size=50),
                    'product_uom_qty' : fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
                    'product_uom'     : fields.many2one('product.uom', 'Unit of Measure ', required=True),
                    'price_unit'      : fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
                    'tax_id'          : fields.many2many('account.tax', 'order_template_tax', 'order_line_id', 'tax_id', 'Taxes',),
                    'discount'        : fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
                    'price_subtotal'  : fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
    }
    _defaults = {
                    'product_uom_qty': 1,
    }

    def product_id_change(self, cr, uid, ids, product_id, inv_type, context=None):
        res = {}
        
        if product_id:
           product = self.pool.get('product.product').browse(cr, uid, product_id)
           res = {'name'    : product.name, 'product_uom': product.uom_id.id, 'price_unit': product.list_price}
           if inv_type == 'in_invoice':
               res['price_unit']  = product.standard_price,
               res['product_uom'] = product.uom_po_id.id
        return {'value': res} 

sale_order_line_template()

class sale_order_template(osv.osv):
    _name = "sale.order.template"
    _description = "Template Sale Order Line"

    _columns = {
        'name'               : fields.char('Template Reference', size=64, required=True),
        'sub_doc_id'         : fields.many2one('subscription.subscription', size=30),
        'subcription_doc_id' : fields.many2one('subscription.document', 'Subscription Doc', required=True, ondelete="cascade", size=128),
        'sale_order_line'    : fields.one2many('sale.order.line.template', 'order_temp_id', 'Order Lines'),
        'date_order'         : fields.date('Date', required=True,),
        'recurring_record'   : fields.boolean('Recurring'),
        'model_name'         : fields.char('Model Name', size=64),
        'partner_id'         : fields.many2one('res.partner', 'Customer', change_default=True, select=True, track_visibility='always'),
        'pricelist_id'       : fields.many2one('product.pricelist', 'Pricelist', required=False, help="Pricelist for current sales order."),
        'invoice_type'       : fields.selection([('out_invoice','Customer Invoice'),('in_invoice','Supplier Invoice')], 'Invoice Type', size=40),
        'company_id'         : fields.many2one('res.company', 'Company'),
    }

    _defaults = {  
                    'name'       : '/',
                    'date_order' : fields.date.context_today,
    }

    def onchange_sub_doc(self, cr, uid, ids, sub_doc_id, context=None):
        ret_val = {'value': {'model_name': ''}}
        if sub_doc_id:
            ret_val['value']['model_name'] = self.pool.get('subscription.document').browse(cr, uid, sub_doc_id).model.model
        return ret_val

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        if not order_lines or order_lines == [(6, 0, [])]:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning, 'value': value}


    def write(self, cr, uid, ids, vals, context=None):
        print "\n\nwrite <s.o.tmpl> :: subscpt_extnd ::vals",vals
        print "write <s.o.tmpl> :: subscpt_extnd ::read",self.read(cr, uid, ids)
        so_tmplt_brw = self.browse(cr, uid, ids)
        subscription_obj = self.pool.get('subscription.subscription')
        search_ids = subscription_obj.search(cr, uid, [('template_order_id','=', ids[0])])
        for_line_ids = []
        # updated = super(sale_order_template, self).write(cr, uid, ids, vals, context=context)
        if search_ids :
            subscription = subscription_obj.browse(cr, uid, search_ids)
            print "\nwrite <s.o.tmpl> :: sbscpt_extnd search ",search_ids
            print "\nwrite <s.o.tmpl> :: sbscpt_extnd ::browse subscription ",subscription
            print "\nwrite <s.o.tmpl> :: sbscpt_extnd ::browse using template_order_id",subscription.template_order_id,\
                        " sub_doc_id",subscription.template_order_id.sub_doc_id,\
                        " recurring_record",subscription.template_order_id.recurring_record
            for_line_ids.append(subscription.template_order_id.id)
            print "\nwrite <s.o.tmpl> :: sbscpt_extnd ::browse using template_ids1",subscription.template_ids1,\
                        " sub_doc_id",subscription.template_ids1.sub_doc_id,\
                        " recurring_record",subscription.template_ids1.recurring_record
            for_line_ids.append(subscription.template_ids1.id)
            # if subscription.template_order_id and subscription.template_order_id.recurring_record \
            #         and not subscription.template_order_id.sub_doc_id:
            #     print "\nwrite <s.o.tmpl> :: sbscpt_extnd inside if for  template_order_id "
            #     self.write(cr, uid, [subscription.template_order_id.id], {'sub_doc_id':search_ids[0]})
            # if subscription.template_ids1 and not subscription.template_ids1.recurring_record \
            #         and subscription.template_ids1.sub_doc_id:
            #     print "\nwrite <s.o.tmpl> :: sbscpt_extnd inside if for  template_ids1 "
            #     self.write(cr, uid, [subscription.template_ids1.id], {'recurring_record':True})
        for_line_ids = list(set(for_line_ids))
        print "for_line_ids",for_line_ids
        so_line_tmpl_obj = self.pool.get('sale.order.line.template')
        if vals.has_key('sale_order_line'):
            sale_order_line = vals.get('sale_order_line')
            print "sale_order_line ",sale_order_line
            for line in sale_order_line:
                print "line",line
                if line[0] == 1 and line[1] in for_line_ids:
                    so_line_tmpl_obj.write(cr,uid, for_line_ids, line[2])

             # vals.delete('sale_order_line')

        updated = super(sale_order_template, self).write(cr, uid, ids, vals, context=context)
        subscription = subscription_obj.browse(cr, uid, search_ids)
        print "\nwrite <s.o.tmpl> :: sbscpt_extnd ::after writing new_datda browse using template_order_id",subscription.template_order_id,\
                    " sub_doc_id",subscription.template_order_id.sub_doc_id,\
                    " recurring_record",subscription.template_order_id.recurring_record

        print "\nwrite <s.o.tmpl> :: sbscpt_extnd ::after writing new_datda browse using template_ids1",subscription.template_ids1,\
                    " sub_doc_id",subscription.template_ids1.sub_doc_id,\
                    " recurring_record",subscription.template_ids1.recurring_record
        #     print "\nwrite <s.o.tmpl> :: subscpt_extnd :: inside if condition"
        if search_ids:
            context['from_SOT'] = True
            subscription_obj.set_done(cr, uid, search_ids, context=context)
            subscription_obj.set_draft(cr, uid, search_ids, context=context)
            subscription_obj.set_process(cr, uid, search_ids, context=context)
        # print "\n 5/0 \n ",5/0,"\n\n"
        # print "\nwrite <s.o.tmpl> :: subscpt_extnd ::end"
        return updated


    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if context.get('doc_id',False):
            vals['sub_doc_id'] = context['doc_id']
        
        print "\n\ncreate <s.o.tmpl> :: subscpt_extnd ::vals",vals, "\n:: context",context," \n\n"
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order.template') or '/'
        
#         print "\n 5/0 \n ",5/0,"\n\n"
        return super(sale_order_template, self).create(cr, uid, vals, context=context)    
sale_order_template()
