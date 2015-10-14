# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler
from kayako import KayakoAPI
from kayako import Ticket,Department

class generate_invoice_for_tasks(osv.osv_memory):
    _name = "generate.invoice.for.tasks"
    _columns = {
                
                
    }

    def generate_invoice(self, cr, uid, ids, context=None):
        task_pool = self.pool.get('project.task')

        tasks_to_invoice = {}
        
        for task in task_pool.browse(cr, uid, context['active_ids']):
            if task.partner_id.id not in tasks_to_invoice:  
                tasks_to_invoice[task.partner_id.id] = []
            tasks_to_invoice[task.partner_id.id].append(task.id)
            
        for partner_id, task_ids in tasks_to_invoice.iteritems():   
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)

            account_id = partner and partner.property_account_receivable.id or False
            if not account_id:
                raise osv.except_osv(('Error'),('Please set default accounts for Partner!'))
            
            invoice_id = self.pool.get('account.invoice').create(cr, uid, {'partner_id' : partner.parent_id and  partner.parent_id.id or partner.id , 'account_id' : account_id,})

            for task in task_pool.browse(cr, uid, task_ids):
                if task.invoiced:
                    continue

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
                                                                               'name' : str(task.kayako_ticket_displayid) +':'+ str(task.name)+work_note,
                                                                               'account_id' : product_account,
                                                                               'quantity' : work.hours or 1.0,
                                                                               'price_unit' : product.list_price or 0.0,
                                                                           })
                    
                    self.pool.get('project.task').write(cr, uid, [task.id], {'invoiced' : True, 'update_state':True, 'stage_id':task.kayako_config_id.export_state and task.kayako_config_id.export_state.id or task.stage_id.id })


generate_invoice_for_tasks()