#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Ramo',]

__metaclass__ = PoolMeta

class Ramo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.ramo'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

