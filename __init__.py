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
        CiaProductoComisiones,
        GrupoPoliza,
        Movimiento,
        ComentarioPoliza,
        OrigenPoliza,
        Poliza,
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
        module='corseg', type_='model')
