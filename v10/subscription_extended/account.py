
from odoo import models, fields


class account_invoice(models.Model):
    _inherit = "account.invoice"
    _columns = {
                    'comment': fields.Text('Notes'),
    }
account_invoice()
