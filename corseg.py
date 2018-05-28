#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Bool, Equal, Not, In
from trytond.modules.company.model import (
        CompanyMultiValueMixin, CompanyValueMixin)

__all__ = [
        'Asegurado', 'Extendido', 'Certificado',
        'CiaProducto', 'CiaSeguros',
        'ComisionCia', 'CiaTipoComision',
        'ComisionVendedor', 'VendedorTipoComision',
        'FormaPago', 'FrecuenciaPago', 'GrupoPoliza',
        'Movimiento', 'Poliza', 'Ramo', 'TipoComision',
        'VehiculoMarca', 'VehiculoModelo', 'Vendedor',
        'Comentario', 'InclusionExclusion',
        'IncluExcluCertificado',
    ]

STATES = [
    ('nuevo', 'Nuevo'),
    ('renovado', 'Renovado'),
    ('moroso', 'Moroso'),
    ('cancelado', 'Cancelado'),
    ('reconsideracion', 'En Reconsideracion'),
    ('suspendido', 'Suspendido'),
    ('reactivado', 'Reactivado'),
]


class CiaSeguros(ModelSQL, ModelView):
    'Compania de Seguros'
    __name__ = 'corseg.cia'
    party = fields.Many2One('party.party', 'Entidad', required=True,
            ondelete='CASCADE')
    productos = fields.One2Many('corseg.cia.producto',
        'cia', 'Productos')
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

    def get_rec_name(self, name):
        return self.party.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('party.rec_name',) + tuple(clause[1:])]


class Ramo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.ramo'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class TipoComision(ModelSQL, ModelView):
    'Tipo Comision'
    __name__ = 'corseg.tipo_comision'
    name = fields.Char('Nombre', required=True)
    tipo = fields.Selection([
            ('fijo', 'Monto Fijo'),
            ('porcentaje', 'Porcentaje'),
        ], 'Tipo', required=True)
    monto = fields.Numeric('Monto', digits=(16, 2))
    description = fields.Char('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class CiaProducto(ModelSQL, ModelView):
    'Producto Compania de Seguros'
    __name__ = 'corseg.cia.producto'
    name = fields.Char('Nombre', required=True)
    cia = fields.Many2One(
            'corseg.cia', 'Compania de Seguros', required=True)
    ramo = fields.Many2One(
            'corseg.ramo', 'Ramo', required=True)
    comision_cia = fields.One2Many('corseg.comision.cia',
        'producto', 'Tabla Comision')
    comision_vendedor = fields.One2Many('corseg.comision.vendedor',
        'producto', 'Tabla Comision Vendedor')
    es_colectiva = fields.Boolean('Colectiva')
    description = fields.Text('Descripcion', size=None)
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


class GrupoPoliza(ModelSQL, ModelView):
    'Grupo de Polizas'
    __name__ = 'corseg.poliza.grupo'
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    name = fields.Char('Nombre', required=True)
    parent = fields.Many2One('corseg.poliza.grupo', 'Parent', select=True)
    childs = fields.One2Many('corseg.poliza.grupo',
        'parent', 'Children', readonly=True)
    polizas = fields.One2Many('corseg.poliza',
        'grupo', 'Polizas', readonly=True)
    description = fields.Char('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        if self.parent:
            return self.parent.get_rec_name(name) + '/' + self.name
        return self.name


class Poliza(ModelSQL, ModelView):
    'Poliza de seguros'
    __name__ = 'corseg.poliza'
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    grupo = fields.Many2One(
            'corseg.poliza.grupo', 'Grupo',
            domain=[('company', '=', Eval('company'))],
            depends=['company']
        )

    # TODO readonly: If(Eval('state'), True, False) 
    cia = fields.Many2One('corseg.cia',
        'Compania de Seguros', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new', 'draft'])),
            },
        depends=['state'])
    cia_producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new', 'draft'])),
            },
        domain=[
            If(
                Bool(Eval('cia')),
                [('cia', '=', Eval('cia'))], []
            )
        ],
        depends=['cia', 'state'])
    # TODO ramo -> function
    numero = fields.Char('Numero de Poliza', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new', 'draft'])),
            },
        depends=['state'])

    contratante = fields.Many2One('party.party', 'Contratante', readonly=True)
    f_emision = fields.Date('Emitida el',  readonly=True)
    f_desde = fields.Date('Desde',  readonly=True)
    f_hasta = fields.Date('Hasta',  readonly=True)
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, 2),  readonly=True)
    prima = fields.Numeric('Prima',
        digits=(16, 2),  readonly=True)
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor', readonly=True)
    notas = fields.Text('Notas', size=None)
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago',  readonly=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago',  readonly=True)
    no_cuotas = fields.Integer('Cant. cuotas', readonly=True)

#    TODO pagos = function
#    TODO pagos_cache = fields.Numeric('Pagos', digits=(16, 2))
#    # TODO function -> saldo = fields.Numeric('Saldo', digits=(16, 2))

#   TODO comision_cia
#   TODO comision_vendedor

#    certificados = fields.One2Many('corseg.poliza.certificado',
#        'poliza', 'Certificados', readonly=True)
    movimientos = fields.One2Many('corseg.poliza.movimiento',
        'poliza', 'Movimientos',
        states={
            'invisible': Equal(Eval('state'), 'new'),
            },
        depends=['state'])
    comentarios = fields.One2Many('corseg.poliza.comentario',
        'poliza', 'Comentarios')

    # TODO pagos
    # TODO comentarios

    # TODO renovacion - readonly, empieza en 0 para polizas nuevas
    
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('draft', 'Borrador'),
            ('activa', 'Activa'),
            ('finiquito', 'Finiquito')
        ],
        'Estado', readonly=True, required=True)

    #TODO unique(cia_producto, numero)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'new'

    @fields.depends('company', 'cia', 'cia_producto')
    def on_change_company(self):
        self.cia = None
        self.cia_producto = None

    @fields.depends('cia_producto')
    def on_change_cia(self):
        self.cia_producto = None

    @fields.depends('cia', 'cia_producto')
    def on_change_cia_producto(self):
        if self.cia_producto:
            self.cia = self.cia_producto.cia

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            values['state'] = 'draft'
        polizas = super(Poliza, cls).create(vlist)
        return polizas


class Certificado(ModelSQL, ModelView):
    'Certificado'
    __name__ = 'corseg.poliza.certificado'
#    inclu_exclu = fields.Many2One('corseg.poliza.inclu_exclu', 'Inclusiones / Exclusiones', required=True,
#            ondelete='CASCADE')
    poliza = fields.Function(fields.Many2One('corseg.poliza', 'Poliza'),
        'get_poliza', searcher='search_poliza')
    numero = fields.Char('Numero de Certificado', required=True)
    asegurado = fields.Many2One('corseg.poliza.asegurado', 'Asegurado', required=True,
            ondelete='CASCADE')
#    extendidos = fields.One2Many('corseg.poliza.extendido',
#        'certificado', 'Extendidos')
    notas = fields.Char('Notas', size=None)
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('incluido', 'Incluido'),
            ('excluido', 'Excluido')
        ], 'Estado', required=True, readonly=True)

    # TODO datos tecnicos

    @staticmethod
    def default_state():
        return 'new'

    def get_rec_name(self, name):
        return self.numero + '-' + self.asegurado.rec_name

    def get_poliza(self, name):
        if self.inclu_exclu:
            return self.inclu_exclu.movimiento.poliza

    @classmethod
    def search_poliza(polizas, name, clause):
        print(polizas)
        print(name)
        print(clause)


class Asegurado(ModelSQL, ModelView):
    'Asegurado'
    __name__ = 'corseg.poliza.asegurado'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    certificados = fields.One2Many('corseg.poliza.certificado',
        'asegurado', 'Certificados', readonly=True)
    # TODO reclamos

    def get_rec_name(self, name):
        return self.party.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('party.rec_name',) + tuple(clause[1:])]


class Extendido(ModelSQL, ModelView):
    'Beneficiario / Dependiente / Conductor adicional'
    __name__ = 'corseg.poliza.extendido'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
#    certificado = fields.One2Many('corseg.poliza.certificado',
#        'asegurado', 'Certificados', readonly=True)
    # TODO parentesco
    # TODO inclusion, exclusion ? seria el id del movimiento
    # TODO state : activo, excluido

    def get_rec_name(self, name):
        return self.party.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('party.rec_name',) + tuple(clause[1:])]


class Vendedor(ModelSQL, ModelView):
    'Vendedor'
    __name__ = 'corseg.vendedor'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    alias = fields.Char('Alias')
    comision = fields.One2Many('corseg.comision.vendedor',
        'vendedor', 'Tabla Comision', readonly=True)
    emisiones = fields.One2Many('corseg.emision',
        'vendedor', 'Polizas', readonly=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

    def get_rec_name(self, name):            
        return self.party.rec_name if not self.alias else self.alias

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = ['OR']
        domain.append(('party.rec_name', clause[1], clause[2]))
        domain.append(('alias', clause[1], clause[2]))
        return domain


class Movimiento(ModelSQL, ModelView):
    'Movimiento de Poliza'
    __name__ = 'corseg.poliza.movimiento'
    poliza = fields.Many2One(
            'corseg.poliza', 'Poliza', required=True)
    fecha = fields.Date('Fecha', required=True)
    descripcion = fields.Char('Descripcion', required=True)
    tipo = fields.Selection([('normal', 'Normal'), ('endoso', 'Endoso')], 'Tipo', required=True)

    contratante = fields.Many2One('party.party', 'Contratante')
    f_emision = fields.Date('Emitida el')
    f_desde = fields.Date('Desde')
    f_hasta = fields.Date('Hasta')
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, 2), required=True)
    prima = fields.Numeric('Prima',
        digits=(16, 2), required=True)
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor', required=True)
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago', required=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago', required=True)
    no_cuotas = fields.Integer('Cant. cuotas')

    renovacion = fields.Boolean('Renovacion')
    finiquito = fields.Boolean('Finalizacion') # TODO Cambiar nombre a finalizacion

    inclu_exclu = fields.One2Many('corseg.poliza.inclu_exclu',
        'movimiento', 'Inclusion / Exclusion')

    comentario = fields.Text('Comentarios', size=None)

    # TODO renovacion - correlativo de renovaciones

    # TODO order by fecha
    #   advertir si una historia tiene fecha menor a la ultima.


class InclusionExclusion(ModelSQL, ModelView):
    'Inclusion /  Exclusion'
    __name__ = 'corseg.poliza.inclu_exclu'
    movimiento = fields.Many2One(
            'corseg.poliza.movimiento', 'Movimiento', required=True)
    poliza = fields.Function(fields.Many2One('corseg.poliza', 'Poliza'),
        'get_poliza', searcher='search_poliza')
    tipo = fields.Selection([
            ('inclusion', 'Inclusion'),
            ('exclusion', 'Exclusion')
        ], 'Tipo', required=True)
    certificado = fields.One2One(
            'corseg.inclu_exclu-certificado', 'inclu_exclu', 'certificado', 'Certificado',
            domain=[
                If(
                    In(Eval('tipo'), ['inclusion']),
                    ['OR',
                        ('state', '=', 'new'),
                        [
                            ('poliza', '=', Eval('poliza')),
                            ('state', '=', 'excluido'),
                        ]
                    ],
                    [
                        ('poliza', '=', Eval('poliza')),
                        ('state', '=', 'incluido')
                    ]
                )
            ],
            depends=['poliza', 'tipo']
    )

#    certificado = fields.Many2One(
#            'corseg.poliza.certificado', 'Certificado', required=True,
#            domain=[
#                If(
#                    In(Eval('tipo'), ['inclusion']),
#                    ['OR',
#                        ('state', '=', 'new'),
#                        [
#                            ('inclu_exclu', '=', Eval('id')),
#
#                            ('state', '=', 'excluido'),
#                        ]
#                    ],
#                    [
#                        ('inclu_exclu', '=', Eval('id')),
#                        ('state', '=', 'incluido')
#                    ]
#                )
#            ],
#            depends=['id', 'tipo']
#        )

    @classmethod
    def create(cls, vlist):
        inclu_exclus = super(InclusionExclusion, cls).create(vlist)
        for ie in inclu_exclus:
            if ie.tipo == 'inclusion':
                if ie.certificado.state not in ['new', 'excluido']:
                    raise Exception(
                        "El certificado debe estar en un estado 'Nuevo' o 'Excluido' " \
                        "para poder ser incluido.")
                ie.certificado.state = 'incluido'
            elif ie.tipo == 'exclusion':
                if ie.certificado.state not in ['incluido']:
                    raise Exception(
                        "El certificado debe estar en un estado 'Incluido' " \
                        "para poder ser excluido.")
                ie.certificado.state = 'excluido'
            ie.certificado.save()
        return inclu_exclus

    def get_poliza(self, name):
        if self.movimiento:
            return self.movimiento.poliza

    def search_poliza(self, name, clause):
        print(name)
        print(clause)


class IncluExcluCertificado(ModelSQL):
    'InclusionExclusion / Certificado'
    __name__ = 'corseg.inclu_exclu-certificado'
    certificado = fields.Many2One('corseg.poliza.certificado', 'Certificado',
        ondelete='CASCADE', select=True, required=True)
    inclu_exclu = fields.Many2One('corseg.poliza.inclu_exclu', 'Inclusion / Exclusion',
        ondelete='CASCADE', select=True, required=True)


class Comentario(ModelSQL, ModelView):
    'Comentarios sobre la Poliza'
    __name__ = 'corseg.poliza.comentario'
    poliza = fields.Many2One(
            'corseg.poliza', 'Poliza', required=True)
    fecha = fields.Date('Fecha', required=True)
    comentario = fields.Text('Comentario', size=None)


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


class FormaPago(ModelSQL, ModelView):
    'Tipo Pago'
    __name__ = 'corseg.forma_pago'
    name = fields.Char('Nombre', required=True)

    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class FrecuenciaPago(ModelSQL, ModelView):
    'Frecuencia Pago'
    __name__ = 'corseg.frecuencia_pago'
    name = fields.Char('Nombre', required=True)
    meses = fields.Integer('Meses', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True
