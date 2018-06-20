#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.company.model import (
        CompanyMultiValueMixin, CompanyValueMixin)

__all__ = [
        'TipoComision',
        'ComisionCia', 'CiaTipoComision',
        'ComisionVendedor', 'VendedorTipoComision',
    ]


class TipoComision(ModelSQL, ModelView):
    'Tipo Comision'
    __name__ = 'corseg.tipo_comision'
    name = fields.Char('Nombre', required=True)
    tipo = fields.Selection([
            ('fijo', 'Monto Fijo'),
            ('porcentaje', 'Porcentaje'),
        ], 'Tipo', required=True)
    monto = fields.Numeric('Monto', digits=(16, 2)) # TODO currency_digits
    description = fields.Char('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class ComisionCia(ModelSQL, ModelView, CompanyMultiValueMixin):
    'Tabla Comision Cia'
    __name__ = 'corseg.comision.cia'
    producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True)
    renovacion = fields.Integer('Renovacion', required=True)
    tipo_comision = fields.MultiValue(fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True))
    tipo_cia_comision = fields.One2Many(
        'corseg.cia.tipo_comision', 'comision_cia', 'Tipo Comision')
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")

    # TODO order by renovacion

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'tipo_comision'}:
            return pool.get('corseg.cia.tipo_comision')
        return super(ComisionCia, cls).multivalue_model(field)


class CiaTipoComision(ModelSQL, CompanyValueMixin):
    "Cia Tipo Comision"
    __name__ = 'corseg.cia.tipo_comision'
    comision_cia = fields.Many2One(
        'corseg.comision.cia', 'Comision Cia',
        ondelete='CASCADE', select=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True)


class ComisionVendedor(ModelSQL, ModelView, CompanyMultiValueMixin):
    'Tabla Comision Vendedor'
    __name__ = 'corseg.comision.vendedor'
    producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True)
    cia_name = fields.Function(fields.Char('Cia'), 'get_cia_name')
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        required=True, ondelete='CASCADE')
    renovacion = fields.Integer('Renovacion', required=True)
    tipo_comision = fields.MultiValue(fields.Many2One('corseg.tipo_comision',
            'Tipo Comision', required=True))
    tipo_vendedor_comision = fields.One2Many(
        'corseg.vendedor.tipo_comision', 'comision_vendedor', 'Tipo Comision')
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")

    # TODO order by vendedor, renovacion

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'tipo_comision'}:
            return pool.get('corseg.vendedor.tipo_comision')
        return super(ComisionVendedor, cls).multivalue_model(field)

    def get_cia_name(self, name):
        if self.producto:
            return self.producto.cia.rec_name


class VendedorTipoComision(ModelSQL, CompanyValueMixin):
    "Vendedor Tipo Comision"
    __name__ = 'corseg.vendedor.tipo_comision'
    comision_vendedor = fields.Many2One(
        'corseg.comision.vendedor', 'Comision Vendedor',
        ondelete='CASCADE', select=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True)
