# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Not, Bool

__all__ = ['Party', 'PartyReplace']


class Party:
    __metaclass__ = PoolMeta
    __name__ = 'party.party'

    is_contratante = fields.Boolean('Es Contratante', readonly=True)
    polizas = fields.One2Many('corseg.poliza',
        'contratante', 'Polizas', readonly=True,
        states={
            'invisible': Not(Bool(Eval('is_contratante'))),
        }, depends=['is_contratante'])

    @classmethod
    def __register__(cls, module_name):
        super(Party, cls).__register__(module_name)

        Partys = Pool().get('party.party')
        parties = Partys.search([])
        Partys.set_is_contratante(parties)

    def _get_is_contratante(self):
        pool = Pool()
        Poliza = pool.get('corseg.poliza')
        if self.id:
            polizas = Poliza.search_read([
                    ('contratante', '=', self.id),
                ], fields_names=['id'])
            if polizas:
                return True

    @classmethod
    def set_is_contratante(cls, parties):
        for party in parties:
            party.is_contratante = party._get_is_contratante()
            party.save()

#    @classmethod
#    def search_is_contratante(cls, name, clause):
#        pool = Pool()
#        Poliza = pool.get('corseg.poliza')
#        Party = pool.get('party.party')
#        result = []
#        v = clause[2]
#        parties = Party.search_read([], fields_names=['id'])
#        for party in parties:
#            polizas = Poliza.search_read([
#                ('contratante', '=', party['id']),
#            ], fields_names=['id'])

#            if v and polizas:
#                result.append(party['id'])
#            elif not v and not polizas:
#                result.append(party['id'])

#        return ['id', 'in', result]


class PartyReplace:
    __metaclass__ = PoolMeta
    __name__ = 'party.replace'

    @classmethod
    def fields_to_replace(cls):
        return super(PartyReplace, cls).fields_to_replace() + [
                ('corseg.cia', 'party'),
                ('corseg.poliza', 'contratante'),
                ('corseg.vendedor', 'party'),
                ('corseg.poliza.certificado', 'asegurado'),
                ('corseg.poliza.certificado.extension', 'extendido'),
                ('corseg.poliza.movimiento', 'contratante'),
                ('corseg.poliza.certificado.modificacion', 'asegurado'),
            ]
