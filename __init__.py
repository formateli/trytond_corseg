# This file is part of trytond-corseg module.
# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from .corseg import *


def register():
    Pool.register(
        Asegurado,
        Beneficiario,
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
        Poliza,
        Inclusion,
        Exclusion,
        Ramo,
        TipoComision,
        VehiculoMarca,
        VehiculoModelo,
        Vendedor,
        module='corseg', type_='model')
