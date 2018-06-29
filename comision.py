#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Not, In
from trytond.modules.company.model import CompanyValueMixin
from .tools import auditoria_field, get_current_date, set_auditoria

__all__ = [
        'TipoComision',
        'Comision',
        'ComisionLinea',
        'ComisionVendedor',
        'ComisionVendedorLinea',
        'ComisionPolizaCia',
        'ComisionPolizaVendedor',
        'ComisionMovimientoCia',
        'ComisionMovimientoVendedor',
        'CiaProductoComisiones',
        'ComisionAjusteCia',
        'ComisionAjusteCiaCompensacion',
        'ComisionAjusteVendedor',
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
        'parent', 'Lineas')
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class ComisionLinea(ComisionBaseLinea):
    'Comision Linea'
    __name__ = 'corseg.comision.linea'
    parent = fields.Many2One('corseg.comision',
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


class ComisionPolizaCia(ComisionBaseLinea):
    'Comision Poliza Cia'
    __name__ = 'corseg.comision.poliza.cia'
    parent = fields.Many2One('corseg.poliza',
        'Poliza', required=True)


class ComisionPolizaVendedor(ComisionBaseLinea):
    'Comision Poliza Vendedor'
    __name__ = 'corseg.comision.poliza.vendedor'
    parent = fields.Many2One('corseg.poliza',
        'Poliza', required=True)


class ComisionMovimientoCia(ComisionBaseLinea):
    'Comision Movimiento Cia'
    __name__ = 'corseg.comision.movimiento.cia'
    parent = fields.Many2One('corseg.poliza.movimiento',
        'Movimiento', required=True)


class ComisionMovimientoVendedor(ComisionBaseLinea):
    'Comision Movimiento Vendedor'
    __name__ = 'corseg.comision.movimiento.vendedor'
    parent = fields.Many2One('corseg.poliza.movimiento',
        'Movimiento', required=True)


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


class ComisionAjusteCia(Workflow, ModelSQL, ModelView):
    'Ajuste de Comision Cia'
    __name__ = 'corseg.comision.ajuste.cia'

    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numero', size=None, readonly=True, select=True)
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    pago = fields.Many2One(
        'corseg.poliza.pago', 'Pago', required=True,
        domain=[
            ('company', '=', Eval('company')),
            If(
                In(Eval('state'), ['borrador',]),
                ('state', '=', 'confirmado'),
                ('state', '!=', '')
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['company', 'state'])
    #TODO liq_cia -> function
    currency = fields.Many2One('currency.currency',
        'Moneda', required=False, readonly=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    compensaciones = fields.One2Many(
        'corseg.comision.ajuste.cia.compensacion',
        'ajuste', 'Compensaciones', readonly=True)
    monto = fields.Numeric('Monto', required=True,
        digits=(16, Eval('currency_digits', 2)),
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['currency_digits'])
    monto_compensado = fields.Function(fields.Numeric('Monto',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']), 'get_monto_compensado')
    monto_pendiente = fields.Function(fields.Numeric('Monto',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']), 'get_monto_pendiente')
    monto_compensado_cache = fields.Numeric('Monto Compensado',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    monto_pendiente_cache = fields.Numeric('Monto Pendiente',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('procesado', 'Procesado'),
            ('confirmado', 'Confirmado'),
            ('pendiente', 'Pendiente'),
            ('compensado', 'Compensado'),
            ('finalizado', 'Finalizado'),
        ], 'Estado', required=True, readonly=True)
    made_by = auditoria_field('user', 'Creado por')
    made_date = auditoria_field('date', 'fecha')
    finalizado_by = auditoria_field('user', 'Finalizado por')
    finalizado_date = auditoria_field('date', 'fecha')

    @classmethod
    def __setup__(cls):
        super(ComisionAjusteCia, cls).__setup__()
        cls._order = [
                ('fecha', 'DESC'),
                ('number', 'DESC'),
            ]
        cls._error_messages.update({
                'delete_borrador': ('El Ajuste "%s" debe estar '
                    'en "Borrador" antes de eliminarse.'),
                })
        cls._transitions |= set(
            (
                ('pendiente', 'finalizado'),
            )
        )
        cls._buttons.update({
            'finalizar': {
                'invisible': Not(In(Eval('state'), ['pendiente'])),
                },
            })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'borrador'

    def get_currency_digits(self, name=None):
        if self.currency:
            self.currency.digits
        return 2

    @fields.depends('pago', 'currency', 'currency_digits')
    def on_change_pago(self):
        self.currency = None
        self.currency_digits = 2
        if self.pago:
            self.currency = self.pago.currency
            self.currency_digits = self.pago.currency_digits

    @classmethod
    def set_number(cls, ajustes):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('corseg.configuration')
        config = Config(1)
        for ajuste in ajustes:
            if ajuste.number:
                continue
            ajuste.number = Sequence.get_id(
                config.ajuste_comision_cia_seq.id)
        cls.save(ajustes)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        ajustes = super(ComisionAjusteCia, cls).create(vlist)
        return ajustes

    @classmethod
    def delete(cls, ajustes):
        for ajuste in ajustes:
            if ajuste.state not in ['borrador',]:
                cls.raise_user_error('delete_borrador', (ajuste.rec_name,))
        super(ComisionAjusteCia, cls).delete(ajustes)

    @classmethod
    @ModelView.button
    @Workflow.transition('finalizado')
    def finalizar(cls, ajustes):
        for ajuste in ajustes:
            set_auditoria(ajuste, 'finalizado')
            ajuste.save()


class ComisionAjusteCiaCompensacion(ModelSQL, ModelView):
    'Ajuste de Comision Cia Compensacion'
    __name__ = 'corseg.comision.ajuste.cia.compensacion'

    ajuste = fields.Many2One('corseg.comision.ajuste.cia',
        'Ajuste', ondelete='CASCADE', select=True, required=True)
    monto = fields.Numeric('Monto', required=True,
        digits=(16, Eval('_parent_currency_digits', 2)))


class ComisionAjusteVendedor(Workflow, ModelSQL, ModelView):
    'Ajuste de Comision Vendedor'
    __name__ = 'corseg.comision.ajuste.vendedor'

    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numero', size=None, readonly=True, select=True)
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    pago = fields.Many2One(
        'corseg.poliza.pago', 'Pago', required=True,
        domain=[
            ('company', '=', Eval('company')),
            If(
                In(Eval('state'), ['borrador',]),
                ('state', '=', 'liq_cia'),
                ('state', '!=', '')
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['company', 'state'])
    #TODO liq_vendedor -> function
    currency = fields.Many2One('currency.currency',
        'Moneda', required=False, readonly=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    monto = fields.Numeric('Monto', required=True,
        digits=(16, Eval('currency_digits', 2)),
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['currency_digits'])
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('procesado', 'Procesado'),
            ('confirmado', 'Confirmado'),
        ], 'Estado', required=True, readonly=True)
    made_by = auditoria_field('user', 'Creado por')
    made_date = auditoria_field('date', 'fecha')

    @classmethod
    def __setup__(cls):
        super(ComisionAjusteVendedor, cls).__setup__()
        cls._order = [
                ('fecha', 'DESC'),
                ('number', 'DESC'),
            ]
        cls._error_messages.update({
                'delete_borrador': ('El Ajuste "%s" debe estar '
                    'en "Borrador" antes de eliminarse.'),
                })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'borrador'

    @fields.depends('pago', 'currency', 'currency_digits')
    def on_change_pago(self):
        self.currency = None
        self.currency_digits = 2
        if self.pago:
            self.currency = self.pago.currency
            self.currency_digits = self.pago.currency_digits

    def get_currency_digits(self, name=None):
        if self.currency:
            self.currency.digits
        return 2

    @classmethod
    def set_number(cls, ajustes):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('corseg.configuration')
        config = Config(1)
        for ajuste in ajustes:
            if ajuste.number:
                continue
            ajuste.number = Sequence.get_id(
                config.ajuste_comision_vendedor_seq.id)
        cls.save(ajustes)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        ajustes = super(ComisionAjusteVendedor, cls).create(vlist)
        return ajustes

    @classmethod
    def delete(cls, ajustes):
        for ajuste in ajustes:
            if ajuste.state not in ['borrador',]:
                cls.raise_user_error('delete_borrador', (ajuste.rec_name,))
        super(ComisionAjusteVendedor, cls).delete(ajustes)
