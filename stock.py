##############################################################################
#
# Copyright (c) 2010-2012 NaN Projectes de Programari Lliure, S.L.
#                         All Rights Reserved.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv

class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    # stock.move
    def _calc_qc_test_input_vals(self, cr, uid, move, context):
        reference = 'stock.production.lot,%d' % move.prodlot_id.id
        return {
            'object_id': reference,
        }
    
    # stock.move
    def _calc_qc_test_trigger_ids_input_vals(self, cr, uid, move, trigger_id, 
            context):
        if (not move.picking_id or move.picking_id.type != 'in' or 
                not move.prodlot_id or move.prodlot_id.state != 'draft' or
                trigger_id in 
                        [x.id for x in move.prodlot_id.qc_trigger_ids] or
                trigger_id not in 
                        [x.id for x in move.product_id.qc_trigger_ids]):
                return False
        
        qc_test_proxy = self.pool.get('qc.test')
        test_trigger_vals = []
        for template_trigger in move.product_id.qc_template_trigger_ids:
            if template_trigger.trigger_id.id != trigger_id:
                continue
            
            test_vals = self._calc_qc_test_input_vals(cr, uid, move, context)
            test_id = qc_test_proxy.create(cr, uid, test_vals, context)
            
            qc_test_proxy.set_test_template(cr, uid, [test_id], 
                    template_trigger.template_id.id, context)
            
            test_trigger_vals.append((0, 0,  {
                        'sequence': template_trigger.sequence,
                        'trigger_id': template_trigger.trigger_id.id,
                        'template_type': template_trigger.template_type,
                        'test_id': test_id,
                    }))
        return test_trigger_vals
    
    
    # stock.move
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        
        move_id = super(stock_move, self).create(cr, uid, vals, context)
        
        if 'input' in context.get('no_create_trigger_test',[]):
            return move_id
        
        input_trigger_id = self.pool.get('qc.trigger').search(cr, uid, 
                [('name','=','Input')], context=context)
        if not input_trigger_id:
            return move_id
        
        move = self.browse(cr, uid, move_id, context)
        if (not move.picking_id or move.picking_id.type != 'in' or 
                not move.prodlot_id):
            return move_id
        
        self.pool.get('stock.production.lot').create_qc_test_triggers(cr, uid, 
                move.prodlot_id, input_trigger_id[0], True, context)
        
        return move_id
    
    
    # stock.move
    def write(self, cr, uid, ids, vals, context=None):
        prodlot_proxy = self.pool.get('stock.production.lot')
        
        res = super(stock_move, self).write(cr, uid, ids, vals, 
                context)
        
        if 'input' in context.get('no_create_trigger_test',[]):
            return res
        
        input_trigger_id = self.pool.get('qc.trigger').search(cr, uid, 
                [('name','=','Input')], context=context)
        if not input_trigger_id:
            return res
        
        for move in self.browse(cr, uid, ids, context):
            if (not move.picking_id or move.picking_id.type != 'in' or 
                    not move.prodlot_id):
                continue
            prodlot_proxy.create_qc_test_triggers(cr, uid, move.prodlot_id, 
                    input_trigger_id[0], True, context)
        
        return res
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
