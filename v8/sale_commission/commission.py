from openerp.osv import osv,fields

class sale_commission_term(osv.osv):
    _name = 'sale.commission.term'
    _columns = {
                    'name'            : fields.char('Name',size=55),
                    'commission_rate' : fields.float('Commission Rate'),
    }
sale_commission_term()

class sale_commission(osv.osv):

    def _cal_gross_profit(self, cr, uid, ids, field, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = line.amount_total - (line.amount_tax + line.cost_of_goods)
        return res
    
    def _cal_commission(self, cr, uid, ids, field, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = 0
            if line.comm_rate_id:
                res[line.id] = line.amount_gross *  ( line.comm_rate_id.commission_rate / 100.0 )
        return res
    
    _name = 'sale.commission'
    _columns = {
                   'invoice_id'    : fields.many2one('account.invoice','Invoice'),
                   'partner_id'    : fields.related('invoice_id', 'partner_id', type="many2one", relation="res.partner", string="Customer", readonly=True),
                   'date_invoice'  : fields.related('invoice_id', 'date_invoice', type="date", string='Date Invoiced', readonly=True),
                   'cost_of_goods' : fields.related('invoice_id', 'cost_of_goods', type="float", string='Cost of Goods'),
                   'comm_rate_id'  : fields.related('invoice_id', 'comm_rate_id', type="many2one", relation='sale.commission.term', string='Commission Rate'),
                   'comm_move_id'  : fields.related('invoice_id', 'comm_move_id', type="many2one", relation="account.move", string="Commission Journal Entry"),
                   
                   'user_id'       : fields.related('invoice_id', 'user_id', type="many2one", relation='res.users', string='Salesman', store=True),
                   'user_partner_id' : fields.related('invoice_id', 'user_partner_id', type="many2one", relation="res.partner", store=True, string="Salesperson"),
                   
                   'amount_total'  : fields.float('Amount'),
                   'amount_tax'    : fields.float('Tax'),
                   'amount_gross'  : fields.function(_cal_gross_profit, type='float', string='Gross Profit'),
                   'amount_comm'   : fields.function(_cal_commission, type='float', string="Commission")
    }

    def unlink(self, cr, uid, ids, context=None):
        for comm in self.browse(cr, uid, ids):
            if comm.comm_move_id:
                raise osv.except_osv('Can not delete', 'First cancel all accounting entries')
        return super(sale_commission, self).unlink(cr, uid, ids, context)

sale_commission()

