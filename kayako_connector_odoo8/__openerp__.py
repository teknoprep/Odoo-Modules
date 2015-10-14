# -*- encoding: utf-8 -*-
{

    'name'        : 'Kayako',  
    'version'     : '3.5',
    'category'    : 'Kayako',
    'summary'     : "Kayako Connector",
    'description' : """ Kayako """,
    "depends"     : ['base','project','account','hr','project_timesheet'],
    'author'      : 'ZedeS Technologies',
    'website'     : 'http://www.zedestech.com',

    'data' : [
              
                       "wizard/generate_invoice.xml",
                       "wizard/generate_invoice_for_tasks.xml",
                       
                       "kayako_view.xml",
                       "project_view.xml",
                       "partner_view.xml",
                       
                       'cron.xml',
                       
                       'security/ir.model.access.csv',
    ],

    'installable': True,
    'auto_install': False,
}