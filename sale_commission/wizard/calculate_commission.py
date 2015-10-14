from openerp.osv import osv,fields

class calculate_sale_commission(osv.osv_memory):
    _name = 'calculate.sale.commission'
    _columns = {
                    'user_id'          : fields.many2one('res.users','Salesperson'),
                    'comm_line_ids'    : fields.one2many('cal.sale.commission.line','cal_comm_id','Sale Commission Lines'),
    }
    
    def show_commissions(self, cr, uid, ids, context=None):
        inv_pool = self.pool.get('account.invoice')
        com_line_pool = self.pool.get('cal.sale.commission.line')

        args = [('state','=','paid'),('comm_move_id','=',False),('no_commission','=',False),('commission_paid','=',False)]
        sobj = self.browse(cr, uid, ids)

        com_ids = com_line_exist_ids = com_line_pool.search(cr, uid, [('cal_comm_id','=',sobj.id)])
        com_line_pool.unlink(cr, uid, com_ids)

        if sobj.user_id:
            args.append( ('user_id','=',sobj.user_id.id) )
        
        
        inv_ids = inv_pool.search(cr, uid, args)
        for invoice in inv_pool.browse(cr, uid, inv_ids):
            amount_total = sum([l.price_subtotal for l in invoice.invoice_line if not l.product_id.commission_not_appl])
            amount_tax   = sum([l.tax_subtotal for l in invoice.invoice_line if not l.product_id.commission_not_appl])
            
            vals = {
                        'cal_comm_id'  : sobj.id, 
                        'invoice_id'   : invoice.id,
                        'user_id'      : invoice.user_id.id, 
                        'amount_total' : amount_total + amount_tax, 
                        'amount_tax'   : amount_tax, 
            }

            com_line_pool.create(cr, uid, vals)
            
        return {
                    'name'      : 'Calculate Commission',
                    'type'      : 'ir.actions.act_window',
                    'res_model' : 'calculate.sale.commission',
                    'view_mode' : 'form',
                    'view_type' : 'form',
                    'res_id'    : ids[0],
                    'target'    : 'new',
            }

    def generate_entries(self, cr, uid, ids, context=None):
        sobj = self.browse(cr, uid, ids[0])
        comm_pool = self.pool.get('sale.commission')
        move_pool = self.pool.get('account.move')
        for comm_line in sobj.comm_line_ids:
            
            if comm_line.amount_comm == 0:
                continue
            
            if not comm_line.user_id.property_account_payable_user or not comm_line.user_id.property_account_commission_user:
                raise osv.except_osv('Please Configure User Account', 'Please configure commission accounts in users configuration')
            
            move_vals= {'date': '2015-02-15', 'journal_id': 1, 'line_id': []}                
            if comm_line.amount_comm >= 0 :
                move_vals['line_id'].append([0,0,{
                                                'account_id' : comm_line.user_id.property_account_payable_user.id, 
                                                'credit'     : comm_line.amount_comm, 
                                                'name'       : comm_line.invoice_id.number, 
                                                'partner_id' : comm_line.user_id.partner_id.id
                                            }])
                move_vals['line_id'].append([0,0,{
                                                'account_id' : comm_line.user_id.property_account_commission_user.id, 
                                                'debit'      : comm_line.amount_comm,
                                                'name'       : comm_line.invoice_id.number, 
                                                'partner_id' : comm_line.user_id.partner_id.id
                                            }])
            else:
                move_vals['line_id'].append([0,0,{
                                                'account_id' : comm_line.user_id.property_account_commission_user.id, 
                                                'credit'     : comm_line.amount_comm * -1, 
                                                'name'       : comm_line.invoice_id.number, 
                                                'partner_id' : comm_line.user_id.partner_id.id
                                            }])
                move_vals['line_id'].append([0,0,{
                                                'account_id' : comm_line.user_id.property_account_payable_user.id, 
                                                'debit'      : comm_line.amount_comm * -1,
                                                'name'       : comm_line.invoice_id.number, 
                                                'partner_id' : comm_line.user_id.partner_id.id
                                            }])
                
            
            print move_vals
            move_id = move_pool.create(cr, uid, move_vals)
            move_pool.button_validate(cr, uid, [move_id])
            
            comm_line.invoice_id.write({'comm_move_id': move_id})
            
            vals = {
                        'invoice_id'   : comm_line.invoice_id.id, 
                        'user_id'      : comm_line.user_id.id, 
                        'amount_total' : comm_line.amount_total, 
                        'amount_tax'   : comm_line.amount_tax, 
                        'comm_move_id' : move_id,
            }
            comm_pool.create(cr, uid, vals)
        
calculate_sale_commission()

class cal_sale_commission_line(osv.osv_memory):
    
    def _cal_amount(self, cr, uid, ids, field, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = {'amount_gross':0, 'amount_comm':0}
            res[line.id]['amount_gross'] = line.amount_total - (line.amount_tax + line.cost_of_goods)
            if line.comm_rate_id:
                res[line.id]['amount_comm'] = res[line.id]['amount_gross'] *  ( line.comm_rate_id.commission_rate / 100.0 )
        return res
    
    _name = 'cal.sale.commission.line'
    _columns = {
                   'cal_comm_id'   : fields.many2one('calculate.sale.commission','Calculate Sale Commission'),
                   'invoice_id'    : fields.many2one('account.invoice','Invoice'),
                   'partner_id'    : fields.related('invoice_id', 'partner_id', type="many2one", relation="res.partner", string="Customer"),
                   'date_invoice'  : fields.related('invoice_id', 'date_invoice', type="date", string='Date Invoiced'),
                   'cost_of_goods' : fields.related('invoice_id', 'cost_of_goods', type="float", string='Cost of Goods'),
                   'comm_rate_id'  : fields.related('invoice_id', 'comm_rate_id', type="many2one", relation='sale.commission.term', string='Commission Rate'),
                   
                   'user_id'       : fields.related('invoice_id', 'user_id', type="many2one", relation='res.users', string='Salesman'),
                   
                   'amount_total'  : fields.float('Amount'),
                   'amount_tax'    : fields.float('Tax'),
                   'amount_gross'  : fields.function(_cal_amount, type='float', string='Gross Profit', multi="amount"),
                   'amount_comm'   : fields.function(_cal_amount, type='float', string="Commission", multi="amount")

    }
cal_sale_commission_line()