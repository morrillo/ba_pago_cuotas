import logging
import psycopg2
import time
from datetime import datetime

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
import openerp.addons.product.product
import math

class pos_make_payment(osv.osv_memory):
	_inherit = 'pos.make.payment'

	_columns = {
		'total_amount': fields.float('Monto total con recargos')
		}

	def check(self, cr, uid, ids, context=None):
		context = context or {}
	        order_obj = self.pool.get('pos.order')
        	active_id = context and context.get('active_id', False)

	        order = order_obj.browse(cr, uid, active_id, context=context)
	        amount = order.amount_total - order.amount_paid
        	data = self.read(cr, uid, ids, context=context)[0]
		cuotas = None
		if data['cuotas_id']:
			cuotas = self.pool.get('sale.cuotas').browse(cr,uid,data['cuotas_id'][0])
			if cuotas:
				vals_line = {
					'product_id': cuotas.product_id.id,
					'order_id': context['active_id'],
					'display_name': cuotas.name,
					'qty': 1,
					'price_unit': amount * cuotas.coeficiente,
					'price_subtotal': amount * cuotas.coeficiente,
					}
				line_id = self.pool.get('pos.order.line').create(cr,uid,vals_line)
				if cuotas.coeficiente > 0:
					vals = {
						'amount': amount * (1+cuotas.coeficiente)
						}
					data['amount'] = amount * (1+cuotas.coeficiente)
					return_id = self.pool.get('pos.make.payment').write(cr,uid,ids,vals)
		res = super(pos_make_payment,self).check(cr,uid,ids,context)
		if cuotas:
			total_amount = amount * ( 1 + cuotas.coeficiente )
			statement_id = self.pool.get('account.bank.statement.line').\
				search(cr,uid,[('pos_statement_id','=',context['active_id']),\
					('journal_id','=',data['journal_id'][0])],order='id desc',limit=1)
			if statement_id:
				statement = self.pool.get('account.bank.statement.line').browse(cr,uid,statement_id)
				if math.floor(statement.amount) == math.floor(total_amount):
					vals = {
						'nro_cupon': data.get('nro_cupon','N/A'),				
						'nro_tarjeta': data.get('nro_tarjeta','N/A'),				
						}
					return_id = self.pool.get('account.bank.statement.line').write(cr,uid,statement_id,vals)
		return {'type': 'ir.actions.act_window_close'}

