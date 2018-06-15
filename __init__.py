# This file is part of trytond-corseg module.
# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from .corseg import *
from .vehiculo import *
from .movimiento import *
from .pago import *
from .liquidacion import *


def register():
    Pool.register(
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
        ComisionCia,
        CiaTipoComision,
        ComisionVendedor,
        VendedorTipoComision,
        FormaPago,
        FrecuenciaPago,
        GrupoPoliza,
        Movimiento,
        Comentario,
        Origen,
        Poliza,
        Ramo,
        TipoComision,
        VehiculoMarca,
        VehiculoModelo,
        VehiculoTipo,
        Vehiculo,
        VehiculoModificacion,
        Vendedor,
        Pago,
        LiquidacionCia,
        LiquidacionVendedor,
        LiquidacionPagoCia,
        LiquidacionPagoVendedor,
        module='corseg', type_='model')
