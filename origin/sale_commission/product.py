from openerp.osv import osv,fields

class product_template(osv.osv):
    _inherit = 'product.template'
    _columns = {
                    'commission_not_appl'   : fields.boolean('Commission Not Applicable')
    }
    _defaults = {
                    'commission_not_appl'   : False
    }
    
product_template()