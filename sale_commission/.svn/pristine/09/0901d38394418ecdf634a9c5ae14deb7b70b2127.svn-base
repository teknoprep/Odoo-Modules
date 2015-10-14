from openerp.osv import osv,fields

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
                    'cost_of_goods'   : fields.float('Cost of Goods'),
                    'comm_rate_id'    : fields.many2one('sale.commission.term', 'Commission Rate'),
                    'comm_move_id'    : fields.many2one('account.move', string="Commission Journal Entry", readonly=True),
                    'no_commission'   : fields.boolean('No Commission on this Invoice'),
                    'commission_paid' : fields.boolean('Commission Paid'),

                    'user_id'         : fields.many2one('res.users', string='Salesperson', readonly=False ),
                    'user_partner_id' : fields.related('user_id', 'partner_id', type="many2one", relation="res.partner", store=True, string="Salesperson")
    }
    _defaults = {
                    'no_commission' : False,
                    'commission_paid' : False
    }

    def onchange_commission(self, cr, uid, ids, salesperson_id, context=None):
        ret_val = {'value': {}}
        if salesperson_id:
            salesperson = self.pool.get('res.users').browse(cr, uid, salesperson_id)
            if salesperson.commission_id:
                ret_val['value']['comm_rate_id'] = salesperson.commission_id.id
        return ret_val
account_invoice()

class account_invoice_line(osv.osv):

    def _cal_tax_subtotal(self, cr, uid, ids, field, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = False
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_id.compute_all(price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id] = sum([t['amount'] for t in taxes.get('taxes',[])])
        return res

    _inherit = 'account.invoice.line'
    _columns = {
                    'tax_subtotal': fields.function(_cal_tax_subtotal, type='float', string="Tax Subtotal")
    }
account_invoice_line()

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
                
    }
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        print "Prepare invoice method called"
        resp = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        resp['comm_rate_id'] = order.user_id and order.user_id.commission_id.id or False
        return resp

sale_order()