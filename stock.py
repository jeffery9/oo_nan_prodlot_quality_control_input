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
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        move_id = super(stock_move, self).create(cr, uid, vals, context)

        if 'input' in context.get('no_create_trigger_test', []):
            return move_id

        input_trigger_id = self.pool.get('qc.trigger').search(cr, uid, [
                    ('name', '=', 'Input'),
                ], context=context)
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
        if context is None:
            context = {}

        prodlot_proxy = self.pool.get('stock.production.lot')

        res = super(stock_move, self).write(cr, uid, ids, vals, context)

        # we will try to create 'test triggers' only when Lot and/or Picking is
        # setted to Stock Move
        if not 'prodlot_id' in vals and not 'picking_id' in vals:
            return res

        if 'input' in context.get('no_create_trigger_test', []):
            return res

        input_trigger_id = self.pool.get('qc.trigger').search(cr, uid, [
                    ('name', '=', 'Input'),
                ], context=context)
        if not input_trigger_id:
            return res

        input_trigger_id = input_trigger_id[0]
        for move in self.browse(cr, uid, ids, context):
            if (not move.picking_id or move.picking_id.type != 'in' or
                    not move.prodlot_id):
                continue
            for test_trigger in move.prodlot_id.qc_test_trigger_ids:
                if test_trigger.trigger_id.id == input_trigger_id:
                    break
            else:
                # If it comes here, the previous 'FOR' has not break =>
                #    no test trigger for 'input_trigger_id'
                prodlot_proxy.create_qc_test_triggers(cr, uid, move.prodlot_id,
                        input_trigger_id, True, context)
        return res
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
