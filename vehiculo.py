#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Equal

__all__ = [
        'VehiculoMarca',
        'VehiculoModelo',
        'VehiculoTipo',
        'Vehiculo',
        'VehiculoModificacion',
    ]

_STATES = {
        'readonly': Not(Equal(Eval('certificado_state'), 'new'))
    }
    
_DEPENDS = ['certificado_state']


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


# TODO crear la clase VehiculoBase de la cual
# se deriven Vehiculo y VehiculoModificacion 

class Vehiculo(ModelSQL, ModelView):
    'Vehiculo'
    __name__ = 'corseg.vehiculo'
    certificado = fields.Many2One('corseg.poliza.certificado',
        'Certificado', ondelete='CASCADE', select=True,
        required=False) # TODO debe ser True despues de la migracion
    placa = fields.Char('Placa',
        states=_STATES, depends=_DEPENDS)
    marca = fields.Many2One('corseg.vehiculo.marca', 'Marca',
        states=_STATES, depends=_DEPENDS)
    modelo = fields.Many2One('corseg.vehiculo.modelo', 'Modelo',
        states=_STATES, depends=_DEPENDS)
    ano = fields.Char('Ano',
        states=_STATES, depends=_DEPENDS)
    s_motor = fields.Char('Motor',
        states=_STATES, depends=_DEPENDS)
    s_carroceria = fields.Char('Carroceria',
        states=_STATES, depends=_DEPENDS)
    color = fields.Char('Color',
        states=_STATES, depends=_DEPENDS)
    transmision = fields.Selection([
            (None, ''),
            ('automatica', 'Automatica'),
            ('manual', 'Manual'),
        ], 'Transmision',
        states=_STATES, depends=_DEPENDS)
    uso = fields.Selection([
            (None, ''),
            ('particular', 'Particular'),
            ('comercial', 'Comercial'),
        ], 'Uso',
        states=_STATES, depends=_DEPENDS)
    tipo = fields.Many2One('corseg.vehiculo.tipo', 'Tipo',
        states=_STATES, depends=_DEPENDS)
    comentario = fields.Text('Comentarios', size=None,
        states=_STATES, depends=_DEPENDS)
    certificado_state = fields.Function(
        fields.Char('Estado del Certificado'),
        'get_certificado_state')

    @staticmethod
    def default_certificado_state():
        return 'new'

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

    def get_certificado_state(self, name):
        if self.certificado:
            return self.certificado.state
        return 'new'


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
            (None, ''),
            ('automatica', 'Automatica'),
            ('manual', 'Manual'),
        ], 'Transmision'
    )
    uso = fields.Selection([
            (None, ''),
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
