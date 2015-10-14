# -*- encoding: utf-8 -*-
from openerp.osv import osv,fields
from openerp.tools.translate import _

class generate_invoice(osv.osv_memory):
    _name = 'generate.invoice'
    _columns = {
                    'partner_ref' : fields.selection([('primary', 'Primary'), ('secondary', 'Secondary')], 'Invoiced To',help="On selection of Organization will generate the invoice on account of Organization if any organization belongs to the customer else it will generate the invoice to the customer directly"),
                    'task_ids'    : fields.many2many('project.task', 'generate_inv_task_rel', 'wiz_id', 'task_id', 'Tasks'),
                    'contact_id'  : fields.many2one('res.partner', 'Contact'),
                    'partner_id'  : fields.many2one('res.partner', 'Customer'),
    }
    
    _defaults = {
                    'partner_ref': 'primary',
    }

    def default_get(self, cr, uid, fields, context=None):
        resp = super(generate_invoice, self).default_get(cr, uid, fields, context)

        project = self.pool.get('project.project').browse(cr, uid, context['active_id'])
        resp['partner_id'] = project.partner_id and project.partner_id.id or False

        task_ids = self.pool.get('project.task').search(cr, uid, [('project_id','=',project.id), ('invoiced','!=', True), ('stage_id.name','=','Billing')])
        if task_ids:
            resp['task_ids'] = [(6, False, task_ids)]

        return resp
    
    def generate_invoice(self, cr, uid, ids, context=None):
        kayako_pool = self.pool.get('kayako.config')
        kayako_ids  = kayako_pool.search(cr, uid, [])
        kayako = kayako_pool.browse(cr, uid, kayako_ids[0])

        sobj = self.browse(cr, uid, ids[0])

        account_id = sobj.partner_id and sobj.partner_id.property_account_receivable.id or False
        if not account_id:
            raise osv.except_osv(('Error'),('Please set default accounts for Partner!'))

        if sobj.partner_id:
            if sobj.partner_ref=='primary':
                partner_id=partner.id
            else:
                partner_id= sobj.contact_id and sobj.contact_id.id or sobj.partner_id.id

            invoice_id = self.pool.get('account.invoice').create(cr, uid, { 'partner_id' : partner_id, 'account_id' : account_id, })

        for task in sobj.task_ids:
            for work in task.work_ids:
                work_note = work.name and '-' + work.name.encode('utf8') or ' '
                product = partner.product_id and partner.product_id or task.kayako_config_id.product_id
                categ_acc_id = product.categ_id and product.categ_id.property_account_income_categ and product.categ_id.property_account_income_categ.id or False 
                product_account = product.property_account_income and product.property_account_income.id or categ_acc_id
                if not product_account:
                    raise osv.except_osv(('Error'),('Please define Income account for product ' + product.name + '!'))

                self.pool.get('account.invoice.line').create(cr, uid, {
                                                                           'invoice_id' : invoice_id,
                                                                           'product_id' : product.id,
                                                                           'name'       : str(task.kayako_ticket_displayid) + ':' + str(task.name) + work_note,
                                                                           'account_id' : product_account,
                                                                           'quantity'   : work.hours or 1.0,
                                                                           'price_unit' : product.list_price or 0.0,
                                                                    })
                self.pool.get('project.task').write(cr, uid, [task.id], {'invoiced' : True, 'update_state':True, 'stage_id':task.kayako_config_id.export_state and task.kayako_config_id.export_state.id or task.stage_id.id })

        return True

generate_invoice()
