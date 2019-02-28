# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Not, Bool

__all__ = ['Party']


class Party:
    __metaclass__ = PoolMeta
    __name__ = 'party.party'

    is_contratante = fields.Function(
        fields.Boolean('Es Contratante'), 'get_is_contratante',
        searcher='search_is_contratante')
    polizas = fields.One2Many('corseg.poliza',
        'contratante', 'Polizas', readonly=True,
        states={
            'invisible': Not(Bool(Eval('is_contratante'))),
        }, depends=['is_contratante'])
        
    def get_is_contratante(self, name):
        pool = Pool()
        Poliza = pool.get('corseg.poliza')
        if self.id:
            polizas = Poliza.search([
                ('contratante', '=', self.id),
            ])
            if polizas:
                return True

    @classmethod
    def search_is_contratante(cls, name, clause):
        pool = Pool()
        Poliza = pool.get('corseg.poliza')
        Party = pool.get('corseg.poliza')
        result = []
        v = clause[2]
        parties = Party.search_read([], fields_names=['id'])
        for party in parties:
            polizas = Poliza.search_read([
                ('contratante', '=', party['id']),
            ], fields_names=['id'])

            if v and polizas:
                result.append(party['id'])
            elif not v and not polizas:
                result.append(party['id'])
        
        return ['id', 'in', result]
