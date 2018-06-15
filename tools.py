#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.model import fields
from trytond.pool import Pool
from trytond.transaction import Transaction

def auditoria_field(type_, string):
    if type_ == 'user':
        return fields.Many2One('res.user', string,
            readonly=True)
    elif type_ == 'date':
        return fields.Date('Fecha', readonly=True)


def get_current_date():
    pool = Pool()
    Date = pool.get('ir.date')
    return Date.today()


def set_auditoria(obj, name):
    setattr(obj, name + '_by', Transaction().user)
    setattr(obj, name + '_date', get_current_date())
