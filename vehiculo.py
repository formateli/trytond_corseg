#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pyson import Eval, If, Bool, Equal, Not, In
from trytond.modules.company.model import (
        CompanyMultiValueMixin, CompanyValueMixin)
from decimal import Decimal

__all__ = [
        'VehiculoMarca',
        'VehiculoModelo',
        'VehiculoTipo',
        'Vehiculo',
        'VehiculoModificacion',
    ]


class VehiculoTipo(ModelSQL, ModelView):
    'Tipo'
    __name__ = 'corseg.vehiculo.tipo'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class VehiculoMarca(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.vehiculo.marca'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class VehiculoModelo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.vehiculo.modelo'
    name = fields.Char('Nombre', required=True)
    marca = fields.Many2One('corseg.vehiculo.marca', 'Marca', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class Vehiculo(ModelSQL, ModelView):
    'Vehiculo'
    __name__ = 'corseg.vehiculo'
    certificado = fields.Many2One('corseg.poliza.certificado',
        'Certificado', ondelete='CASCADE', select=True, required=True)
    placa = fields.Char('Placa')
    marca = fields.Many2One('corseg.vehiculo.marca', 'Marca')
    modelo = fields.Many2One('corseg.vehiculo.modelo', 'Modelo')
    ano = fields.Char('Ano')
    s_motor = fields.Char('Motor')
    s_carroceria = fields.Char('Carroceria')
    color = fields.Char('Color')
    transmision = fields.Selection([
            ('none', ''),
            ('automatica', 'Automatica'),
            ('manual', 'Manual'),
        ], 'Transmision'
    )
    uso = fields.Selection([
            ('none', ''),
            ('particular', 'Particular'),
            ('comercial', 'Comercial'),
        ], 'Uso'
    )
    tipo = fields.Many2One('corseg.vehiculo.tipo', 'Tipo')
    comentario = fields.Text('Comentarios', size=None)

    def get_rec_name(self, name):
        return "{0}/{1}/{2}".format(
            self.marca, self.modelo, self.placa)

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = ['OR']
        domain.append(('marca.rec_name', clause[1], clause[2]))
        domain.append(('modelo.rec_name', clause[1], clause[2]))
        domain.append(('placa', clause[1], clause[2]))
        return domain

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_transmision():
        return 'none'

    @staticmethod
    def default_uso():
        return 'none'


class VehiculoModificacion(ModelSQL, ModelView):
    'Vehiculo Modificacion'
    __name__ = 'corseg.vehiculo.modificacion'
    modificacion = fields.Many2One('corseg.poliza.certificado',
        'Modificacion', ondelete='CASCADE', select=True, required=True)
    placa = fields.Char('Placa')
    marca = fields.Many2One('corseg.vehiculo.marca', 'Marca')
    modelo = fields.Many2One('corseg.vehiculo.modelo', 'Modelo')
    ano = fields.Char('Ano')
    s_motor = fields.Char('Motor')
    s_carroceria = fields.Char('Carroceria')
    color = fields.Char('Color')
    transmision = fields.Selection([
            ('none', ''),
            ('automatica', 'Automatica'),
            ('manual', 'Manual'),
        ], 'Transmision'
    )
    uso = fields.Selection([
            ('none', ''),
            ('particular', 'Particular'),
            ('comercial', 'Comercial'),
        ], 'Uso'
    )
    tipo = fields.Many2One('corseg.vehiculo.tipo', 'Tipo')
    comentario = fields.Text('Comentarios', size=None)

    def get_rec_name(self, name):
        return "{0}/{1}/{2}".format(
            self.marca, self.modelo, self.placa)

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = ['OR']
        domain.append(('marca.rec_name', clause[1], clause[2]))
        domain.append(('modelo.rec_name', clause[1], clause[2]))
        domain.append(('placa', clause[1], clause[2]))
        return domain

    @staticmethod
    def default_transmision():
        return 'none'

    @staticmethod
    def default_uso():
        return 'none'
