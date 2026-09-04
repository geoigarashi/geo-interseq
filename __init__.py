from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qgis.gui import QgisInterface
    from .geo_interseq import GeoInterseQPlugin


def classFactory(iface: QgisInterface) -> GeoInterseQPlugin:
    """Fábrica de classe do QGIS para instanciar o plugin.

    Args:
        iface (QgisInterface): Interface principal do QGIS.

    Returns:
        GeoInterseQPlugin: A instância principal do plugin GeoInterseQPlugin.
    """
    _check_dependencies()
    from .geo_interseq import GeoInterseQPlugin

    return GeoInterseQPlugin(iface)


def _check_dependencies() -> None:
    """Verifica silenciosamente as dependências e registra em log sem interromper o boot do QGIS."""
    try:
        from .dependency_installer import DependencyManager
        from qgis.core import Qgis, QgsMessageLog

        missing: list[str] = DependencyManager.get_missing_dependencies()
        if missing:
            QgsMessageLog.logMessage(
                f"Bibliotecas para análise raster não detectadas: {', '.join(missing)}. "
                "O assistente de instalação com 1 clique estará disponível ao abrir o GeoInterseQ.",
                "GeoInterseQ",
                Qgis.Info,
            )
    except Exception:
        pass

