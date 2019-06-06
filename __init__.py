# This file is part of trytond-corseg module.
# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from . import configuration
from . import corseg
from . import comision
from . import vehiculo
from . import movimiento
from . import pago
from . import liquidacion
from . import reclamo
from . import party


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequences,
        corseg.CiaProducto,
        corseg.CiaSeguros,
        corseg.ComentarioPoliza,
        corseg.OrigenPoliza,
        corseg.PolizaDocumento,
        corseg.Poliza,
        corseg.Renovacion,
        corseg.Ramo,
        corseg.GrupoPoliza,
        corseg.Vendedor,
        comision.TipoComision,
        comision.Comision,
        comision.ComisionLinea,
        comision.ComisionVendedor,
        comision.ComisionVendedorLinea,
        comision.ComisionPolizaCia,
        comision.ComisionPolizaVendedor,
        comision.ComisionMovimientoCia,
        comision.ComisionMovimientoVendedor,
        comision.CiaProductoComisiones,
        comision.ComisionAjusteCia,
        comision.ComisionAjusteCiaCompensacion,
        comision.ComisionAjusteVendedor,
        movimiento.PartyCorseg,
        movimiento.Certificado,
        movimiento.CertificadoInclusion,
        movimiento.CertificadoExclusion,
        movimiento.CertificadoModificacion,
        movimiento.Extension,
        movimiento.ExtendidoInclusion,
        movimiento.ExtendidoExclusion,
        movimiento.Movimiento,
        vehiculo.VehiculoMarca,
        vehiculo.VehiculoModelo,
        vehiculo.VehiculoTipo,
        vehiculo.Vehiculo,
        vehiculo.VehiculoModificacion,
        pago.FormaPago,
        pago.FrecuenciaPago,
        pago.Pago,
        liquidacion.LiquidacionCia,
        liquidacion.LiquidacionVendedor,
        liquidacion.LiquidacionPagoCia,
        liquidacion.LiquidacionPagoVendedor,
        reclamo.Reclamo,
        reclamo.ReclamoComentario,
        reclamo.ReclamoDocumento,
        party.Party,
        module='corseg', type_='model')
    Pool.register(
        party.PartyReplace,
        module='corseg', type_='wizard')
