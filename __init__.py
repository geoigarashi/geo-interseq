# -*- coding: utf-8 -*-
"""Módulo de inicialização do plugin GeoInterseQ para QGIS."""

def classFactory(iface: object) -> object:
    """Fábrica de classe do QGIS para instanciar o plugin.

    Args:
        iface (object): Interface principal do QGIS.

    Returns:
        object: A instância principal do plugin GeoInterseQPlugin.
    """
    _check_dependencies(iface)
    from .geo_interseq import GeoInterseQPlugin
    return GeoInterseQPlugin(iface)


def _check_dependencies(iface: object) -> None:
    """Verifica se as dependências do plugin estão instaladas e exibe um aviso se faltarem.

    Args:
        iface (object): Interface principal do QGIS.
    """
    missing: list[str] = []
    for pkg in ('rasterio', 'shapely', 'pyproj'):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    try:
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.warning(
            iface.mainWindow(),
            'GeoInterseQ — dependências ausentes',
            'As seguintes bibliotecas Python não foram encontradas:\n\n'
            + '\n'.join(f'  • {p}' for p in missing)
            + '\n\nA análise de camadas RASTER não funcionará.\n\n'
            'Para instalar, abra o OSGeo4W Shell como administrador e execute:\n'
            f'  pip install {" ".join(missing)}\n\n'
            'Consulte o arquivo README.md do plugin para mais detalhes.'
        )
    except Exception:
        pass
