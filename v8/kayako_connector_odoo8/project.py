
from openerp.osv import osv, fields

class project_task(osv.osv):
    
    def sync_with_kayako(self, cr, uid, context=None):
        kayako_ids=self.pool.get('kayako.config').search(cr,uid,[('state','=','connected')])   
        self.pool.get('kayako.config').import_ticket(cr, uid, kayako_ids)

        return True

    
    _inherit = 'project.task'
    _columns = {
                    'kayako_ticket_id' : fields.integer('Kayako Ticket Id'),
                    'kayako_ticket_displayid' : fields.char('Kayako Ticket DisplayId',size=128),
                    'kayako_config_id' : fields.many2one('kayako.config', 'Kayako Configuration id'),
                    'invoiced' : fields.boolean('Invoiced'),
                    'active' : fields.boolean('Active'),
                    'update_state':fields.boolean('Reverse Update')
    }
    
project_task()

class project_project(osv.osv):
    _inherit = 'project.project'
    
    def validate_all_invoices(self, cr, uid, ids, context=None):
        inv_pool = self.pool.get('account.invoice')

        for project in self.browse(cr, uid, ids):
            invoice_ids=inv_pool.search(cr, uid, [('partner_id', '=', project.partner_id.id),('state','=','draft')])
            for invoice_id in invoice_ids:
                inv_pool.signal_workflow(cr, uid, [invoice_id], 'invoice_open')        

        return True
project_project()

class project_task_type(osv.osv):
    _inherit='project.task.type'
    _columns = {
                    'kayako_id' : fields.integer('Kayako id'),
    }

project_task_type()

class project_task_work(osv.osv):
    _inherit = 'project.task.work'
    _columns = {
                    'name':fields.char('Name',size=256),
                    'kayako_timetrack_id' : fields.integer('Kayako Timetrack Id'),
    }
    
project_task_work()