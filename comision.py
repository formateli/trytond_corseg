#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.company.model import CompanyValueMixin

__all__ = [
        'TipoComision',
        'Comision',
        'ComisionLinea',
        'ComisionVendedor',
        'ComisionVendedorLinea',
        'CiaProductoComisiones',
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


class ComisionBaseLinea(ModelSQL, ModelView):
    renovacion = fields.Integer('Renovacion', required=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True)
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")
    active = fields.Boolean('Activo')

    @classmethod
    def __setup__(cls):
        super(ComisionBaseLinea, cls).__setup__()
        cls._order = [
                ('renovacion', 'ASC'),
                ('id', 'ASC'),
            ]

    @staticmethod
    def default_active():
        return True


class Comision(ModelSQL, ModelView):
    'Comision'
    __name__ = 'corseg.comision'
    name = fields.Char('Nombre', required=True)
    lineas = fields.One2Many('corseg.comision.linea',
        'comision', 'Lineas')
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class ComisionLinea(ComisionBaseLinea):
    'Comision Linea'
    __name__ = 'corseg.comision.linea'
    comision = fields.Many2One('corseg.comision',
        'Comision', required=True)


class ComisionVendedor(ModelSQL, ModelView):
    'Comision Vendedor'
    __name__ = 'corseg.comision.vendedor'
    name = fields.Char('Nombre', required=True)
    lineas = fields.One2Many('corseg.comision.vendedor.linea',
        'parent', 'Lineas')
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class ComisionVendedorLinea(ModelSQL, ModelView):
    'Comision Vendedor Linea'
    __name__ = 'corseg.comision.vendedor.linea'
    parent = fields.Many2One('corseg.comision.vendedor',
        'Parent', required=True)
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        required=True)
    comision = fields.Many2One('corseg.comision', 'Comision',
        required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class CiaProductoComisiones(ModelSQL, CompanyValueMixin):
    "Cia Producto Comisiones"
    __name__ = 'corseg.comisiones.cia.producto'
    cia_producto = fields.Many2One(
        'corseg.cia.producto', 'Cia Producto',
        ondelete='CASCADE', select=True)
    comision_cia = fields.Many2One(
        'corseg.comision',
        'Comision Cia')
    comision_vendedor = fields.Many2One(
        'corseg.comision.vendedor',
        'Comision Vendedor')
    comision_vendedor_defecto = fields.Many2One(
        'corseg.comision',
        'Comision Vendedor por Defecto')
