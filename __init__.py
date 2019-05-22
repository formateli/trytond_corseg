# This file is part of trytond-corseg module.
# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from .configuration import *
from .corseg import *
from .comision import *
from .vehiculo import *
from .movimiento import *
from .pago import *
from .liquidacion import *
from .reclamo import *
from .party import *


def register():
    Pool.register(
        Configuration,
        ConfigurationSequences,
        PartyCorseg,
        Certificado,
        CertificadoInclusion,
        CertificadoExclusion,
        CertificadoModificacion,
        Extension,
        ExtendidoInclusion,
        ExtendidoExclusion,
        CiaProducto,
        CiaSeguros,
        TipoComision,
        Comision,
        ComisionLinea,
        ComisionVendedor,
        ComisionVendedorLinea,
        ComisionPolizaCia,
        ComisionPolizaVendedor,
        ComisionMovimientoCia,
        ComisionMovimientoVendedor,
        CiaProductoComisiones,
        ComisionAjusteCia,
        ComisionAjusteCiaCompensacion,
        ComisionAjusteVendedor,
        GrupoPoliza,
        Movimiento,
        ComentarioPoliza,
        OrigenPoliza,
        PolizaDocumento,
        Poliza,
        Renovacion,
        Ramo,
        VehiculoMarca,
        VehiculoModelo,
        VehiculoTipo,
        Vehiculo,
        VehiculoModificacion,
        Vendedor,
        FormaPago,
        FrecuenciaPago,
        Pago,
        LiquidacionCia,
        LiquidacionVendedor,
        LiquidacionPagoCia,
        LiquidacionPagoVendedor,
        Reclamo,
        ReclamoComentario,
        ReclamoDocumento,
        Party,
        module='corseg', type_='model')
    Pool.register(
        PartyReplace,
        module='corseg', type_='wizard')
