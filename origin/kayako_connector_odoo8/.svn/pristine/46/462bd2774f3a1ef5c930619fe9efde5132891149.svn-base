
from openerp.osv import osv, fields

class res_partner(osv.osv):
    """ Inherited to add new fields"""
    
    _inherit = 'res.partner'
    _columns = {
                    'kayako_user_id'     : fields.integer('Kayako UserID'),
                    'kayako_organization_id' : fields.integer('Kayako OrganizationID'),
                    'product_id' : fields.many2one('product.product', 'Product'),
                }
    
res_partner()
