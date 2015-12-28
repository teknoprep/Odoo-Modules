from openerp.osv import osv,fields

class res_users(osv.osv):
    _inherit = 'res.users'
    _columns = {
                    'commission_id' : fields.many2one('sale.commission.term','Commission Rate'),
                    'property_account_payable_user': fields.property(type='many2one', relation='account.account', string="Payable Account",
                                                                            help="This account will be used to record Payable"),
                    'property_account_commission_user': fields.property(type='many2one', relation='account.account', string="Commission Account",
                                                                            help="This account will be used to record commissions"),
                
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        resp = super(res_users, self).write(cr, uid, ids, vals, context)
        for user in self.browse(cr, uid, ids):
            pass
        
        return resp
res_users()

class res_partner(osv.osv):
    
    def _comm_total(self, cr, uid, ids, field, args, context=None):
        res = {}
        for partner in self.browse(cr, uid, ids):
            res[partner.id] = {'comm_earned':0, 'comm_paid':0, 'comm_due':0}
            for line in partner.ledger_lines:
                if line.credit>0:
                    res[partner.id]['comm_earned'] += line.credit
                elif line.debit>0: 
                    res[partner.id]['comm_paid'] += line.debit
                
            res[partner.id]['comm_due'] = res[partner.id]['comm_earned'] - res[partner.id]['comm_paid']

        return res
    
    _inherit = 'res.partner'
    _columns = {
                    'is_salesman'      : fields.boolean('Salesman'),
                    
                    'move_lines'       : fields.one2many('account.move.line', 'partner_id', 'Journal Items'),
                    'ledger_lines'     : fields.one2many('account.move.line', 'partner_id', 'Journal Items', domain=[('account_id.type','in',['receivable','payable'])]),
                    
                    'commission_ids'   : fields.one2many('sale.commission', 'user_partner_id', 'Commissions'),
                    'comm_invoice_ids' : fields.one2many('account.invoice', 'user_partner_id', 'Invoices'),
                    'comm_pay_ids'     : fields.one2many('account.voucher', 'partner_id'),
                    
                    'comm_earned'      : fields.function(_comm_total, type='float', string="Commission", multi="comm"),
                    'comm_paid'        : fields.function(_comm_total, type='float', string="Commission Paid", multi="comm"),
                    'comm_due'         : fields.function(_comm_total, type='float', string="Commission Due", multi="comm"),
                    
    }
    
    def create_payment(self, cr, uid, ids, context=None):
        partner = self.browse(cr, uid, ids[0])

        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')


        return {
            'name'        : "Make Commission Payment",
            'view_mode'   : 'form',
            'view_id'     : view_id,
            'view_type'   : 'form',
            'res_model'   : 'account.voucher',
            'type'        : 'ir.actions.act_window',
            'nodestroy'   : True,
            'target'      : 'new',
            'domain'      : '[]',
            'context': {
                            'default_partner_id' : partner.id,
                            'default_amount'     : partner.comm_due,
                            'default_type'       : 'payment',
                            'type'               : 'payment'
            }
        }
    
res_partner()