from trytond.pyson import Eval
from trytond.pool import Pool
from trytond.model import (
    ModelSingleton, ModelView, ModelSQL, fields)
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)

__all__ = ['Configuration', 'ConfigurationSequences']


class Configuration(
        ModelSingleton, ModelSQL, ModelView, CompanyMultiValueMixin):
    'Corseg Configuration'
    __name__ = 'corseg.configuration'
    pago_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Pago Sequence", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.pago'),
        ]))
    movimiento_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Movimiento Sequence", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),

            ('code', '=', 'corseg.movimiento'),
        ]))
    liq_cia_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Liquidacion Cia", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.liquidacion.cia'),
        ]))
    liq_vendedor_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Liquidacion Vendedor", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.liquidacion.vendedor'),
        ]))
    ajuste_comision_cia_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Ajuste Comision Cia", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.comision.ajuste.cia'),
        ]))
    ajuste_comision_vendedor_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Ajuste Comision Vendedor", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.comision.ajuste.vendedor'),
        ]))
    reclamo_seq = fields.MultiValue(fields.Many2One(
        'ir.sequence', "Reclamo Sequence", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.reclamo'),
        ]))


    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'pago_seq', 'movimiento_seq',
                'liq_cia_seq', 'liq_vendedor_seq',
                'ajuste_comision_cia_seq', 'ajuste_comision_vendedor_seq',
                'reclamo_seq'}:
            return pool.get('corseg.configuration.sequences')
        return super(Configuration, cls).multivalue_model(field)


class ConfigurationSequences(ModelSQL, CompanyValueMixin):
    'Configuration Sequences'
    __name__ = 'corseg.configuration.sequences'
    pago_seq = fields.Many2One(
        'ir.sequence', "Pago Sequence", 
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.pago'),
        ])
    movimiento_seq = fields.Many2One(
        'ir.sequence', "Movimiento Sequence", 
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.movimiento'),
        ])
    liq_cia_seq = fields.Many2One(
        'ir.sequence', "Liquidacion Cia",
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.liquidacion.cia'),
        ])
    liq_vendedor_seq = fields.Many2One(
        'ir.sequence', "Liquidacion Vendedor",
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.liquidacion.vendedor'),
        ])
    ajuste_comision_cia_seq = fields.Many2One(
        'ir.sequence', "Ajuste Comision Cia",
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.comision.ajuste.cia'),
        ])
    ajuste_comision_vendedor_seq = fields.Many2One(
        'ir.sequence', "Ajuste Comision Vendedor",
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.comision.ajuste.vendedor'),
        ])
    reclamo_seq = fields.Many2One(
        'ir.sequence', "Reclamo Sequence", 
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'corseg.reclamo'),
        ])
