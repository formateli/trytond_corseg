# This file is part of trytond-corseg module.
# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from .corseg import *
from .vehiculo import *
from .movimiento import *
from .pago import *


def register():
    Pool.register(
        PartyCorseg,
        Certificado,
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
        CertificadoInclusion,
        CertificadoExclusion,
        CertificadoVehiculo,
        Ramo,
        TipoComision,
        VehiculoMarca,
        VehiculoModelo,
        VehiculoTipo,
        Vehiculo,
        Vendedor,
        Pago,
        module='corseg', type_='model')
