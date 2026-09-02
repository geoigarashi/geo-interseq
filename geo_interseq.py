# -*- coding: utf-8 -*-
"""Módulo principal do plugin GeoInterseQ para QGIS.

Calcula a interseção e a porcentagem de sobreposição de camadas vetoriais e raster
dentro de uma camada base de polígonos.
"""

import configparser
from pathlib import Path
import csv
import numpy as np
from osgeo import gdal

from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QMessageBox, QFrame, QInputDialog, QFileDialog,
    QDoubleSpinBox, QWidget, QTextBrowser
)
from qgis.PyQt.QtCore import Qt, QVariant, pyqtSignal, QMimeData
from qgis.PyQt.QtGui import QIcon, QColor, QBrush, QFont, QPixmap, QGuiApplication
from qgis.core import (
    Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsWkbTypes,
    QgsDistanceArea, QgsField, QgsUnitTypes, QgsPointXY,
    QgsPalettedRasterRenderer, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsFillSymbol, QgsFeatureRequest, QgsMapLayer,
    QgsMessageLog
)
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel

try:
    from qgis.PyQt.QtSvg import QSvgWidget
    HAS_SVG_WIDGET: bool = True
except ImportError:
    HAS_SVG_WIDGET: bool = False

gdal.UseExceptions()

PLUGIN_MENU: str = 'Ferramentas Geo'
LAYER_NAME_OUT: str = 'Interseções (GeoInterseQ)'

_TYPE_VECTOR: str = 'Vetor'
_TYPE_RASTER: str = 'Raster'


def _build_footer(plugin_dir: str) -> str:
    """Gera o texto de rodapé com base nos metadados do plugin.

    Args:
        plugin_dir (str): Caminho do diretório do plugin.

    Returns:
        str: Texto formatado do rodapé do diálogo.
    """
    try:
        meta = configparser.ConfigParser()
        meta_path = Path(plugin_dir) / 'metadata.txt'
        meta.read(meta_path, encoding='utf-8')
        name: str = meta.get('general', 'name', fallback='GeoInterseQ')
        version: str = meta.get('general', 'version', fallback='')
        author: str = meta.get('general', 'author', fallback='')
        maintainer: str = meta.get('general', 'maintainer', fallback='')
        parts: list[str] = [f'{name} v{version}' if version else name]
        if author:
            parts.append(author)
        if maintainer and maintainer != author:
            parts.append(maintainer)
        return '  |  '.join(parts)
    except Exception:
        return 'GeoInterseQ'


_QGIS_LAYER_MIME: str = 'application/qgis.layertreemodeldata'


def _layer_from_mime(mime_data: QMimeData) -> QgsMapLayer | None:
    """Extrai QgsMapLayer a partir do mime data arrastado do painel de camadas do QGIS.

    Args:
        mime_data (QMimeData): Dados mime do evento de arrastar e soltar.

    Returns:
        QgsMapLayer | None: A camada do QGIS correspondente ou None caso falhe.
    """
    if not mime_data.hasFormat(_QGIS_LAYER_MIME):
        return None
    try:
        from qgis.PyQt.QtXml import QDomDocument
        doc = QDomDocument()
        doc.setContent(mime_data.data(_QGIS_LAYER_MIME))
        layer_id: str = doc.documentElement().firstChildElement('layer-tree-layer').attribute('id')
        return QgsProject.instance().mapLayer(layer_id)
    except Exception:
        return None


def _accept_copy(event: object) -> None:
    """Aceita o evento forçando CopyAction para não remover a camada do projeto.

    Args:
        event (object): Evento de drag/drop da PyQt.
    """
    event.setDropAction(Qt.CopyAction)
    event.accept()


class _DropLayerComboBox(QgsMapLayerComboBox):
    """QgsMapLayerComboBox com suporte a drag & drop do painel de camadas do QGIS."""

    def __init__(self, parent: object = None) -> None:
        """Inicializa o combo box configurado para aceitar drop.

        Args:
            parent (object, optional): Objeto pai do widget.
        """
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: object) -> None:
        """Manipula o evento de entrada do objeto arrastado.

        Args:
            event (object): Evento de drag enter da PyQt.
        """
        if event.mimeData().hasFormat(_QGIS_LAYER_MIME):
            _accept_copy(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event: object) -> None:
        """Manipula o evento de movimentação do objeto arrastado.

        Args:
            event (object): Evento de drag move da PyQt.
        """
        if event.mimeData().hasFormat(_QGIS_LAYER_MIME):
            _accept_copy(event)
        else:
            event.ignore()

    def dropEvent(self, event: object) -> None:
        """Manipula o evento de soltura do objeto arrastado.

        Args:
            event (object): Evento de drop da PyQt.
        """
        lyr: QgsMapLayer | None = _layer_from_mime(event.mimeData())
        if lyr:
            self.setLayer(lyr)
            _accept_copy(event)
        else:
            event.ignore()


class _DropOverlayList(QListWidget):
    """QListWidget que aceita drag & drop do painel de camadas do QGIS.

    Emite o sinal layerDropped(QgsMapLayer) para o diálogo processar.
    """

    layerDropped: pyqtSignal = pyqtSignal(object)

    def __init__(self, parent: object = None) -> None:
        """Inicializa a lista configurada para aceitar drops.

        Args:
            parent (object, optional): Objeto pai do widget.
        """
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)

    def dragEnterEvent(self, event: object) -> None:
        """Manipula o evento de entrada de arrasto.

        Args:
            event (object): Evento de drag enter.
        """
        if event.mimeData().hasFormat(_QGIS_LAYER_MIME):
            _accept_copy(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event: object) -> None:
        """Manipula o evento de movimentação do arrasto.

        Args:
            event (object): Evento de drag move.
        """
        if event.mimeData().hasFormat(_QGIS_LAYER_MIME):
            _accept_copy(event)
        else:
            event.ignore()

    def dropEvent(self, event: object) -> None:
        """Manipula o evento de soltura (drop).

        Args:
            event (object): Evento de drop.
        """
        lyr: QgsMapLayer | None = _layer_from_mime(event.mimeData())
        if lyr:
            self.layerDropped.emit(lyr)
            _accept_copy(event)
        else:
            event.ignore()


class GeoInterseQDialog(QDialog):
    """Diálogo da interface gráfica para configuração e execução do GeoInterseQ."""

    def __init__(self, iface: object) -> None:
        """Inicializa o diálogo e monta a interface.

        Args:
            iface (object): A interface QGIS (QgisInterface).
        """
        super().__init__(iface.mainWindow())
        self.iface: object = iface
        self.setWindowTitle('GeoInterseQ — Área e % da Analisada dentro da Base')

        # Obter geometria da tela para dimensionamento responsivo
        screen = QGuiApplication.primaryScreen()
        screen_geom = screen.availableGeometry() if screen else None
        screen_w: int = screen_geom.width() if screen_geom else 1920
        screen_h: int = screen_geom.height() if screen_geom else 1080

        # Ajuste dinâmico de altura e escala dos logos baseados na resolução da tela
        dialog_height: int = 620
        h_logo: int = 75

        if screen_h < 768:
            dialog_height = max(500, screen_h - 80)
            h_logo = 60
        elif screen_h < 900:
            h_logo = 70
        else:
            dialog_height = 650
            h_logo = 85

        dialog_width: int = min(1180, screen_w - 40)
        self.resize(dialog_width, dialog_height)

        # Layout horizontal principal (divide controles de ajuda)
        main_layout: QHBoxLayout = QHBoxLayout(self)

        # Painel Esquerdo (Formulário de Controles)
        left_widget: QWidget = QWidget()
        left_layout: QVBoxLayout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.base_combo: _DropLayerComboBox = _DropLayerComboBox()
        self.base_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.base_combo.setToolTip('Selecione pelo combo ou arraste uma camada do painel de Camadas')
        self.chk_base_selected: QCheckBox = QCheckBox('Usar apenas feições selecionadas da base')

        self.overlay_combo: _DropLayerComboBox = _DropLayerComboBox()
        self.overlay_combo.setFilters(
            QgsMapLayerProxyModel.PolygonLayer | QgsMapLayerProxyModel.RasterLayer
        )
        self.btn_add_overlay: QPushButton = QPushButton('Adicionar camada analisada')
        self.overlay_list: _DropOverlayList = _DropOverlayList()
        self.overlay_list.setSelectionMode(self.overlay_list.ExtendedSelection)
        self.overlay_list.setFixedHeight(100)
        self.overlay_list.setToolTip('Arraste camadas do painel de Camadas ou use o botão "Adicionar"')
        self.btn_remove_overlay: QPushButton = QPushButton('Remover selecionadas')

        self.unit_combo: QComboBox = QComboBox()
        self.unit_combo.addItems(['m²', 'hectares', 'km²'])
        self.unit_combo.setCurrentText('hectares')

        self.chk_create_layer: QCheckBox = QCheckBox('Gerar camada de interseção (temporária)')

        self.chk_spatial_filter: QCheckBox = QCheckBox('Filtro espacial vetorial — buffer ao redor da base:')
        self.chk_spatial_filter.setToolTip(
            'Limita a análise vetorial às feições dentro de um buffer ao redor da camada base.\n'
            'Recomendado para camadas grandes (ex: embargos, biomas nacionais).\n'
            'Usa o índice espacial da camada — muito mais rápido que varrer todas as feições.'
        )
        self.spn_buffer_km: QDoubleSpinBox = QDoubleSpinBox()
        self.spn_buffer_km.setRange(0.1, 500.0)
        self.spn_buffer_km.setValue(10.0)
        self.spn_buffer_km.setSuffix(' km')
        self.spn_buffer_km.setDecimals(1)
        self.spn_buffer_km.setEnabled(False)
        self.spn_buffer_km.setFixedWidth(90)
        self.chk_spatial_filter.toggled.connect(self.spn_buffer_km.setEnabled)

        self.chk_paired_mode: QCheckBox = QCheckBox(
            'Modo pareado — interseção restrita por campo-chave e origem'
        )
        self.chk_paired_mode.setToolTip(
            'Ative quando base e camada analisada compartilham um campo-chave (ex: id_par)\n'
            'e um campo de origem (ex: contrato/rcp). A interseção será calculada\n'
            'apenas entre feições de origens opostas dentro do mesmo par.'
        )

        self.table: QTableWidget = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ['Tipo', 'Camada analisada', 'Classe', 'Área de interseção', '%']
        )
        hdr = self.table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setToolTip(
            'Vetor: % da feição analisada dentro da base\n'
            'Raster: % da base coberto pela classe'
        )
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 180)
        self.table.setAlternatingRowColors(True)

        self.btn_run: QPushButton = QPushButton('Calcular')
        self.btn_run.setStyleSheet(
            'QPushButton { background-color: #0078d4; color: white; font-weight: bold;'
            ' border-radius: 4px; padding: 4px 16px; }'
            'QPushButton:hover { background-color: #006abe; }'
            'QPushButton:pressed { background-color: #005a9e; }'
        )
        self.btn_export_csv: QPushButton = QPushButton('Exportar CSV')
        self.btn_export_csv.setEnabled(False)
        self.btn_close: QPushButton = QPushButton('Fechar')

        left_layout.addWidget(QLabel('<b>Camada base (polígonos vetoriais):</b>'))
        left_layout.addWidget(self.base_combo)
        left_layout.addWidget(self.chk_base_selected)

        left_layout.addWidget(QLabel('<b>Camadas analisadas (vetorial ou raster):</b>'))
        hl: QHBoxLayout = QHBoxLayout()
        hl.addWidget(self.overlay_combo)
        hl.addWidget(self.btn_add_overlay)
        left_layout.addLayout(hl)

        hl2: QHBoxLayout = QHBoxLayout()
        hl2.addWidget(self.overlay_list)
        v_btns: QVBoxLayout = QVBoxLayout()
        v_btns.addWidget(self.btn_remove_overlay)
        v_btns.addStretch(1)
        hl2.addLayout(v_btns)
        left_layout.addLayout(hl2)

        hl3: QHBoxLayout = QHBoxLayout()
        hl3.addWidget(QLabel('Unidade de área:'))
        hl3.addWidget(self.unit_combo)
        hl3.addStretch(1)
        hl3.addWidget(self.chk_create_layer)
        left_layout.addLayout(hl3)

        hl4: QHBoxLayout = QHBoxLayout()
        hl4.addWidget(self.chk_spatial_filter)
        hl4.addWidget(self.spn_buffer_km)
        hl4.addStretch(1)
        left_layout.addLayout(hl4)
        left_layout.addWidget(self.chk_paired_mode)

        left_layout.addWidget(QLabel('<b>Resultados:</b>'))
        left_layout.addWidget(self.table, stretch=1)

        hb: QHBoxLayout = QHBoxLayout()
        hb.addWidget(self.btn_export_csv)
        hb.addStretch(1)
        hb.addWidget(self.btn_close)
        hb.addWidget(self.btn_run)
        left_layout.addLayout(hb)

        sep: QFrame = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(sep)

        lbl_footer: QLabel = QLabel(_build_footer(str(Path(__file__).parent)))
        lbl_footer.setAlignment(Qt.AlignCenter)
        lbl_footer.setStyleSheet('color: gray; font-size: 10px;')
        left_layout.addWidget(lbl_footer)

        # Divisor Visual Vertical
        divider: QFrame = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)

        # Painel Direito (Logotipo e Tutorial)
        right_widget: QWidget = QWidget()
        right_layout: QVBoxLayout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 10, 0)
        right_widget.setFixedWidth(280)

        # Logos da Ferramenta e da Plataforma (lado a lado)
        logos_layout = QHBoxLayout()
        logos_layout.addStretch(1)

        logo_path = Path(__file__).parent / 'Logo-GEO-HQ.svg'
        icon_path = Path(__file__).parent / 'icon.png'

        has_any_logo: bool = False

        # 1. Adiciona o ícone do plugin
        if icon_path.exists():
            lbl_icon = QLabel()
            pix_icon = QPixmap(str(icon_path)).scaled(
                h_logo, h_logo, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_icon.setPixmap(pix_icon)
            lbl_icon.setFixedSize(h_logo, h_logo)
            logos_layout.addWidget(lbl_icon)
            has_any_logo = True

        # Adiciona espaçamento se ambos existirem
        if icon_path.exists() and logo_path.exists() and HAS_SVG_WIDGET:
            logos_layout.addSpacing(12)

        # 2. Adiciona o logotipo da plataforma
        if logo_path.exists() and HAS_SVG_WIDGET:
            logo_widget = QSvgWidget(str(logo_path))
            w_logo = int(h_logo * 0.78)
            logo_widget.setFixedSize(w_logo, h_logo)
            logos_layout.addWidget(logo_widget)
            has_any_logo = True

        logos_layout.addStretch(1)

        if has_any_logo:
            right_layout.addLayout(logos_layout)

        # Navegador de Documentação/Tutorial em HTML
        tutorial_browser: QTextBrowser = QTextBrowser()
        tutorial_browser.setReadOnly(True)
        tutorial_browser.setOpenExternalLinks(True)
        tutorial_browser.setStyleSheet(
            "QTextBrowser {"
            " border: 1px solid #c0c0c0;"
            " border-radius: 4px;"
            " padding: 6px;"
            " font-size: 11px;"
            "}"
        )
        
        tutorial_html: str = """
        <h3>GeoInterseQ — Tutorial</h3>
        <p>Calcula interseções de áreas e proporções de sobreposição entre uma camada base e camadas analisadas.</p>
        
        <b>Passo a Passo:</b>
        <ol style="margin-left: -20px; padding-left: 20px;">
          <li><b>Camada Base:</b> Selecione um vetor de polígonos. Marque para usar apenas feições selecionadas se aplicável.</li>
          <li><b>Camada Analisada:</b> Escolha um vetor ou raster e clique em <i>Adicionar</i>. Camadas podem ser arrastadas diretamente da barra lateral do QGIS.</li>
          <li><b>Unidade:</b> Escolha m², hectares (padrão) ou km².</li>
          <li><b>Filtro Espacial:</b> Ative para polígonos grandes e pesados. Cria um buffer indexado ao redor da base, acelerando o processamento.</li>
          <li><b>Calcular:</b> Clique para processar e ver os resultados.</li>
        </ol>
        
        <hr/>
        <b>Dicas Úteis:</b>
        <ul>
          <li><b>Modos de % (Vetor):</b>
            <ul>
              <li><i>% da feição:</i> proporção da área analisada que incide dentro da base.</li>
              <li><i>% da base:</i> proporção da camada base que é ocupada pela feição.</li>
            </ul>
          </li>
          <li><b>Modo Raster:</b> Calcula a área pixel a pixel por classe. Mapeia automaticamente a legenda e cores configuradas no QGIS.</li>
          <li><b>Gerar Camada:</b> Vetores e classes do raster intersectados serão exportados como camadas temporárias no mapa.</li>
        </ul>
        """
        tutorial_browser.setHtml(tutorial_html)
        right_layout.addWidget(tutorial_browser)

        # Montagem dos painéis no layout horizontal principal
        main_layout.addWidget(left_widget, stretch=1)
        main_layout.addWidget(divider)
        main_layout.addWidget(right_widget, stretch=0)

        self.btn_add_overlay.clicked.connect(self.add_overlay)
        self.btn_remove_overlay.clicked.connect(self.remove_overlay)
        self.overlay_list.layerDropped.connect(self.add_overlay)
        self.btn_run.clicked.connect(self.run)
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_close.clicked.connect(self.hide)

    def add_overlay(self, lyr: QgsMapLayer | None = None) -> None:
        """Adiciona uma camada na lista de sobreposições para análise.

        Args:
            lyr (QgsMapLayer | None, optional): A camada de mapa a ser adicionada.
        """
        if not isinstance(lyr, (QgsVectorLayer, QgsRasterLayer)):
            lyr = self.overlay_combo.currentLayer()
        if not isinstance(lyr, (QgsVectorLayer, QgsRasterLayer)):
            return
        for i in range(self.overlay_list.count()):
            if self.overlay_list.item(i).data(Qt.UserRole) == lyr:
                return

        label_field: str | None = None
        pct_relative_to_base: bool = False
        if isinstance(lyr, QgsVectorLayer):
            fields: list[str] = [f.name() for f in lyr.fields()]
            if fields:
                field, ok = QInputDialog.getItem(
                    self,
                    'Campo de rótulo',
                    f'Selecione o campo para identificar cada feição de "{lyr.name()}":',
                    fields,
                    0,
                    False,
                )
                if not ok:
                    return
                label_field = field

            pct_options: list[str] = [
                '% da feição analisada  (ex: quanto da gleba está dentro do imóvel)',
                '% da camada base       (ex: quanto do imóvel está coberto pela feição)',
            ]
            pct_choice, ok = QInputDialog.getItem(
                self,
                'Base do percentual',
                'O % deve ser calculado em relação a qual área?',
                pct_options,
                0,
                False,
            )
            if not ok:
                return
            pct_relative_to_base = pct_choice == pct_options[1]

        paired_key_field: str | None = None
        paired_origin_field: str | None = None
        paired_base_value: str | None = None
        paired_overlay_value: str | None = None

        if isinstance(lyr, QgsVectorLayer) and self.chk_paired_mode.isChecked():
            if not label_field:
                QMessageBox.warning(
                    self, 'Campo de rótulo necessário',
                    'No modo pareado, o campo de rótulo selecionado será usado como\n'
                    'chave de pareamento (ex: id_par). Selecione um campo válido.',
                )
                return
            paired_key_field = label_field

            fields_names: list[str] = [f.name() for f in lyr.fields()]
            origin_f, ok = QInputDialog.getItem(
                self,
                'Campo de origem',
                f'O campo "{paired_key_field}" será usado como chave de pareamento.\n\n'
                'Selecione o campo que distingue os dois lados do par:\n'
                '(ex: origem — contém "contrato" e "rcp")',
                fields_names, 0, False,
            )
            if not ok:
                return
            paired_origin_field = origin_f

            origin_values: list[str] = sorted({
                str(f[paired_origin_field]).strip()
                for f in lyr.getFeatures()
                if f[paired_origin_field] is not None
            })
            if len(origin_values) < 2:
                QMessageBox.warning(
                    self, 'Campo de origem insuficiente',
                    f'O campo "{paired_origin_field}" deve conter pelo menos '
                    f'2 valores distintos.\nEncontrados: {origin_values}',
                )
                return

            if len(origin_values) == 2:
                paired_base_value = origin_values[0]
                paired_overlay_value = origin_values[1]
            else:
                base_val, ok = QInputDialog.getItem(
                    self,
                    'Valor do lado BASE',
                    'O campo de origem possui mais de 2 valores.\n'
                    'Qual valor representa o lado BASE do par?',
                    origin_values, 0, False,
                )
                if not ok:
                    return
                paired_base_value = base_val
                remaining: list[str] = [v for v in origin_values if v != base_val]
                if len(remaining) == 1:
                    paired_overlay_value = remaining[0]
                else:
                    ov_val, ok = QInputDialog.getItem(
                        self,
                        'Valor do lado ANALISADO',
                        'Qual valor representa o lado ANALISADO?',
                        remaining, 0, False,
                    )
                    if not ok:
                        return
                    paired_overlay_value = ov_val

        prefix: str = _TYPE_RASTER if isinstance(lyr, QgsRasterLayer) else _TYPE_VECTOR
        label_info: str = f' [{label_field}]' if label_field else ''
        item: QListWidgetItem = QListWidgetItem(f'[{prefix}] {lyr.name()}{label_info}')
        item.setData(Qt.UserRole, lyr)
        item.setData(Qt.UserRole + 1, label_field)
        item.setData(Qt.UserRole + 2, pct_relative_to_base)
        item.setData(Qt.UserRole + 3, paired_key_field)
        item.setData(Qt.UserRole + 4, paired_origin_field)
        item.setData(Qt.UserRole + 5, paired_base_value)
        item.setData(Qt.UserRole + 6, paired_overlay_value)
        tip_pct: str = '% da camada base' if pct_relative_to_base else '% da feição analisada'
        paired_info: str = (
            f' | Pareado: {paired_key_field}/{paired_origin_field}'
            if paired_key_field else ''
        )
        item.setToolTip(
            'Análise pixel a pixel por classe (raster categórico inteiro)'
            if prefix == _TYPE_RASTER
            else f'Campo de rótulo: {label_field} | {tip_pct}{paired_info}'
        )
        self.overlay_list.addItem(item)

    def remove_overlay(self) -> None:
        """Remove as camadas selecionadas da lista de sobreposições."""
        for it in self.overlay_list.selectedItems():
            self.overlay_list.takeItem(self.overlay_list.row(it))

    def _convert_area(self, area_m2: float) -> float:
        """Converte a área de metros quadrados para a unidade selecionada.

        Args:
            area_m2 (float): Área em metros quadrados.

        Returns:
            float: Área convertida na unidade selecionada.
        """
        u: str = self.unit_combo.currentText()
        if u == 'hectares':
            return area_m2 / 10000.0
        if u == 'km²':
            return area_m2 / 1_000_000.0
        return area_m2

    def _format_area(self, area_m2: float) -> str:
        """Formata o valor da área para exibição textual em padrão brasileiro.

        Args:
            area_m2 (float): Área em metros quadrados.

        Returns:
            str: Texto formatado (ex: "1.234,5678 hectares").
        """
        val: float = self._convert_area(area_m2)
        unit: str = self.unit_combo.currentText()
        return f"{val:,.4f} {unit}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def _insert_result_row(self, layer_type: str, name: str, area_m2: float, percent: float) -> None:
        """Atalho para inserir linha sem especificação de classe.

        Args:
            layer_type (str): Tipo da camada (Vetor/Raster).
            name (str): Nome da camada.
            area_m2 (float): Área de interseção em m².
            percent (float): Percentual da interseção.
        """
        self._insert_result_row_with_class(layer_type, name, '—', area_m2, percent)

    def _insert_result_row_with_class(
        self, layer_type: str, name: str, class_label: str, area_m2: float, percent: float,
        *, warning: bool = False
    ) -> None:
        """Insere uma linha de resultado detalhada na tabela.

        Args:
            layer_type (str): Tipo da camada (Vetor/Raster).
            name (str): Nome da camada analisada.
            class_label (str): Classe ou rótulo da feição.
            area_m2 (float): Área de interseção em m².
            percent (float): Percentual da interseção.
        """
        row: int = self.table.rowCount()
        self.table.insertRow(row)
        pct_text: str = f"{percent:.2f} %" if area_m2 > 0 else '0,00 %'
        for col, text in enumerate([layer_type, name, class_label, self._format_area(area_m2), pct_text]):
            item: QTableWidgetItem = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)

        type_item: QTableWidgetItem = self.table.item(row, 0)
        if layer_type == _TYPE_VECTOR:
            type_item.setBackground(QBrush(QColor('#dbeafe')))
            type_item.setForeground(QBrush(QColor('#1e40af')))
        else:
            type_item.setBackground(QBrush(QColor('#fef3c7')))
            type_item.setForeground(QBrush(QColor('#92400e')))
        bold: QFont = QFont()
        bold.setBold(True)
        type_item.setFont(bold)
        type_item.setTextAlignment(Qt.AlignCenter)

        if warning:
            warn_brush: QBrush = QBrush(QColor('#FFF3CD'))
            for col_idx in range(self.table.columnCount()):
                w_item: QTableWidgetItem | None = self.table.item(row, col_idx)
                if w_item:
                    w_item.setBackground(warn_brush)
                    w_item.setToolTip('⚠ Área de interseção excede a menor gleba do par')

    def run(self) -> None:
        """Executa a análise de interseção espacial espacial baseada nas configurações da GUI."""
        base: QgsMapLayer | None = self.base_combo.currentLayer()
        if not isinstance(base, QgsVectorLayer) or base.geometryType() != QgsWkbTypes.PolygonGeometry:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma camada BASE de POLÍGONOS.')
            return
        if self.overlay_list.count() == 0:
            QMessageBox.warning(self, 'Aviso', 'Adicione pelo menos uma camada analisada.')
            return

        base_feats: list[QgsFeature] = (
            list(base.getSelectedFeatures()) if self.chk_base_selected.isChecked()
            else list(base.getFeatures())
        )
        if not base_feats:
            QMessageBox.warning(self, 'Aviso', 'A camada base não possui feições (ou nenhuma está selecionada).')
            return

        crs_measure: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem('EPSG:4326')
        ctx: object = QgsProject.instance().transformContext()

        base_geoms: list[QgsGeometry] = []
        for f in base_feats:
            g: QgsGeometry = f.geometry()
            if not g or g.isEmpty():
                continue
            g2: QgsGeometry = QgsGeometry(g)
            if base.crs() != crs_measure:
                try:
                    tr = QgsCoordinateTransform(base.crs(), crs_measure, ctx)
                    g2.transform(tr)
                except Exception as e:
                    QMessageBox.critical(self, 'Erro de transformação', f'Falha ao reprojetar base: {e}')
                    return
            base_geoms.append(g2)

        if not base_geoms:
            QMessageBox.critical(self, 'Erro', 'Geometrias inválidas na base.')
            return

        base_union: QgsGeometry = base_geoms[0]
        for g in base_geoms[1:]:
            base_union = base_union.combine(g)
        base_union = base_union.makeValid()

        da: QgsDistanceArea = QgsDistanceArea()
        ell: str = QgsProject.instance().ellipsoid() or 'WGS84'
        da.setEllipsoid(ell)
        da.setSourceCrs(crs_measure, ctx)

        base_area_m2: float = da.measureArea(base_union)

        base_source_wkt_list: list[str] = []
        for f in base_feats:
            g = f.geometry()
            if g and not g.isEmpty():
                base_source_wkt_list.append(g.asWkt())
        base_source_crs: QgsCoordinateReferenceSystem = base.crs()

        self.table.setRowCount(0)
        self.btn_export_csv.setEnabled(False)

        create_layer: bool = self.chk_create_layer.isChecked()

        def _make_out_layer(name: str) -> QgsVectorLayer:
            vl = QgsVectorLayer(
                f"MultiPolygon?crs={crs_measure.authid()}", name, 'memory'
            )
            prov = vl.dataProvider()
            prov.addAttributes([
                QgsField('type', QVariant.String),
                QgsField('layer', QVariant.String),
                QgsField('class', QVariant.String),
                QgsField('area_m2', QVariant.Double),
                QgsField('area_ha', QVariant.Double),
                QgsField('percent', QVariant.Double),
            ])
            vl.updateFields()
            return vl

        vec_out_layer: QgsVectorLayer | None = _make_out_layer(LAYER_NAME_OUT) if create_layer else None
        vec_out_used: bool = False

        spatial_filter_rect: QgsGeometry | None = None
        if self.chk_spatial_filter.isChecked():
            buf_m: float = self.spn_buffer_km.value() * 1000.0
            bbox = base_union.boundingBox()
            bbox.grow(buf_m / 111320.0)
            spatial_filter_rect = bbox

        project = QgsProject.instance()
        group = None
        if create_layer:
            root = project.layerTreeRoot()
            group = root.findGroup("Resultados GeoInterseQ")
            if group is None:
                group = root.insertGroup(0, "Resultados GeoInterseQ")

        for i in range(self.overlay_list.count()):
            lyr: QgsMapLayer | None = self.overlay_list.item(i).data(Qt.UserRole)

            if isinstance(lyr, QgsRasterLayer):
                raster_out: QgsVectorLayer | None = _make_out_layer(f'Interseção — {lyr.name()}') if create_layer else None
                self._process_raster_layer(
                    lyr, base_union, base_area_m2, crs_measure, ctx, raster_out,
                    base_source_wkt_list, base_source_crs
                )
                if raster_out and create_layer:
                    raster_out.updateExtents()
                    project.addMapLayer(raster_out, False)
                    if group:
                        group.addLayer(raster_out)
            elif isinstance(lyr, QgsVectorLayer):
                if lyr.geometryType() != QgsWkbTypes.PolygonGeometry:
                    continue
                label_field: str | None = self.overlay_list.item(i).data(Qt.UserRole + 1)
                pct_relative_to_base: bool = self.overlay_list.item(i).data(Qt.UserRole + 2) or False
                paired_key: str | None = self.overlay_list.item(i).data(Qt.UserRole + 3)
                paired_origin: str | None = self.overlay_list.item(i).data(Qt.UserRole + 4)
                paired_base_val: str | None = self.overlay_list.item(i).data(Qt.UserRole + 5)
                paired_overlay_val: str | None = self.overlay_list.item(i).data(Qt.UserRole + 6)

                if paired_key and paired_origin:
                    self._process_vector_layer_paired(
                        lyr, da, crs_measure, ctx, vec_out_layer,
                        paired_key, paired_origin,
                        paired_base_val, paired_overlay_val,
                        pct_relative_to_base, label_field,
                    )
                else:
                    self._process_vector_layer(
                        lyr, base_union, base_area_m2, label_field,
                        pct_relative_to_base, da, crs_measure, ctx, vec_out_layer,
                        spatial_filter_rect,
                    )
                vec_out_used = True

        if vec_out_layer and vec_out_used:
            vec_out_layer.updateExtents()
            project.addMapLayer(vec_out_layer, False)
            if group:
                group.addLayer(vec_out_layer)

        if self.table.rowCount() > 0:
            self.btn_export_csv.setEnabled(True)

    def export_csv(self) -> None:
        """Exporta os resultados exibidos na tabela para um arquivo CSV delimitado por ';', codificação UTF-8-sig."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Exportar resultados como CSV', '', 'CSV (*.csv)'
        )
        if not path:
            return
        if not path.lower().endswith('.csv'):
            path += '.csv'

        headers: list[str] = [
            self.table.horizontalHeaderItem(c).text()
            for c in range(self.table.columnCount())
        ]
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    writer.writerow([
                        (self.table.item(row, col).text() if self.table.item(row, col) else '')
                        for col in range(self.table.columnCount())
                    ])
            QMessageBox.information(self, 'Exportação concluída', f'Arquivo salvo em:\n{path}')
        except Exception as e:
            QMessageBox.critical(self, 'Erro ao exportar', str(e))

    def _process_vector_layer(
        self, lyr: QgsVectorLayer, base_union: QgsGeometry, base_area_m2: float,
        label_field: str | None, pct_relative_to_base: bool, da: QgsDistanceArea,
        crs_measure: QgsCoordinateReferenceSystem, ctx: object,
        out_layer: QgsVectorLayer | None, spatial_filter_rect: object = None
    ) -> None:
        """Processa a interseção com uma camada vetorial de polígonos.

        Args:
            lyr (QgsVectorLayer): Camada vetorial analisada.
            base_union (QgsGeometry): Geometria unificada da camada base.
            base_area_m2 (float): Área total da camada base em m².
            label_field (str | None): Nome do campo de rótulo para identificação.
            pct_relative_to_base (bool): Se True, calcula % em relação à base. Senão, em relação à feição.
            da (QgsDistanceArea): Ferramenta de cálculo de área com elipsoide do QGIS.
            crs_measure (QgsCoordinateReferenceSystem): CRS para cálculo métrico (WGS84).
            ctx (object): Contexto de transformação do projeto.
            out_layer (QgsVectorLayer | None): Camada de saída para guardar geometrias intersectadas.
            spatial_filter_rect (object, optional): Bounding box opcional para o filtro espacial.
        """
        try:
            tr_ov = QgsCoordinateTransform(lyr.crs(), crs_measure, ctx)
        except Exception as e:
            QMessageBox.critical(self, 'Erro de transformação', f'Falha no CRS da camada {lyr.name()}: {e}')
            return

        if spatial_filter_rect is not None:
            try:
                tr_rect = QgsCoordinateTransform(crs_measure, lyr.crs(), ctx)
                filter_rect = tr_rect.transformBoundingBox(spatial_filter_rect)
            except Exception:
                filter_rect = spatial_filter_rect
            request = QgsFeatureRequest().setFilterRect(filter_rect)
        else:
            request = QgsFeatureRequest()

        for feat in lyr.getFeatures(request):
            g = feat.geometry()
            if not g or g.isEmpty():
                continue
            g2 = QgsGeometry(g)
            try:
                g2.transform(tr_ov)
            except Exception:
                continue
            g2 = g2.makeValid()

            feat_area_m2: float = da.measureArea(g2)

            inter_geom = g2.intersection(base_union)
            inter_geom = inter_geom.makeValid() if inter_geom else None
            inter_area_m2: float = (
                da.measureArea(inter_geom) if inter_geom and not inter_geom.isEmpty() else 0.0
            )

            if inter_area_m2 < 1.0:
                continue

            if pct_relative_to_base:
                denom = base_area_m2
            else:
                denom = feat_area_m2
            percent: float = (inter_area_m2 / denom * 100.0) if denom > 0 else 0.0

            if label_field:
                class_label: str = str(feat[label_field]) if feat[label_field] is not None else f'FID {feat.id()}'
            else:
                class_label = f'FID {feat.id()}'

            self._insert_result_row_with_class(_TYPE_VECTOR, lyr.name(), class_label, inter_area_m2, percent)

            if out_layer and inter_geom and not inter_geom.isEmpty():
                out_feat = QgsFeature()
                out_feat.setGeometry(inter_geom)
                out_feat.setAttributes([
                    _TYPE_VECTOR, lyr.name(), class_label, inter_area_m2, inter_area_m2 / 10000.0, percent
                ])
                out_layer.dataProvider().addFeatures([out_feat])

    def _process_vector_layer_paired(
        self, lyr: QgsVectorLayer, da: QgsDistanceArea,
        crs_measure: QgsCoordinateReferenceSystem, ctx: object,
        out_layer: QgsVectorLayer | None,
        key_field: str, origin_field: str,
        origin_base_value: str, origin_overlay_value: str,
        pct_relative_to_base: bool, label_field: str | None,
    ) -> None:
        """Processa interseção vetorial no modo pareado por campo-chave e origem.

        Itera sobre cada valor único do campo-chave, separa feições por origem
        e calcula a interseção apenas entre origens opostas do mesmo par.

        Args:
            lyr: Camada vetorial contendo ambas origens.
            da: Calculador de área geodésica.
            crs_measure: CRS de medição (EPSG:4326).
            ctx: Contexto de transformação do projeto.
            out_layer: Camada de saída para geometrias intersectadas.
            key_field: Nome do campo-chave de pareamento (ex: 'id_par').
            origin_field: Nome do campo de origem (ex: 'origem').
            origin_base_value: Valor de origem do lado base (ex: 'contrato').
            origin_overlay_value: Valor de origem do lado analisado (ex: 'rcp').
            pct_relative_to_base: Se True, % em relação à base; senão, à feição.
            label_field: Campo de rótulo para a coluna 'class' na tabela.
        """
        from collections import defaultdict

        try:
            tr_ov = QgsCoordinateTransform(lyr.crs(), crs_measure, ctx)
        except Exception as e:
            QMessageBox.critical(
                self, 'Erro de transformação', f'Falha no CRS: {e}'
            )
            return

        # 1. Coletar e reprojetar todas as feições, agrupando por key_field
        groups: dict[str, dict[str, list[QgsGeometry]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for feat in lyr.getFeatures():
            g = feat.geometry()
            if not g or g.isEmpty():
                continue

            key_val = feat[key_field]
            origin_val = feat[origin_field]
            if key_val is None or origin_val is None:
                continue

            key_str: str = str(key_val).strip()
            origin_str: str = str(origin_val).strip().lower()

            g2 = QgsGeometry(g)
            try:
                g2.transform(tr_ov)
            except Exception:
                continue
            g2 = g2.makeValid()

            groups[key_str][origin_str].append(g2)

        origin_base_lower: str = origin_base_value.strip().lower()
        origin_overlay_lower: str = origin_overlay_value.strip().lower()

        # 2. Iterar sobre cada par
        for key_val in sorted(groups.keys()):
            origins = groups[key_val]
            base_geoms: list[QgsGeometry] = origins.get(origin_base_lower, [])
            overlay_geoms: list[QgsGeometry] = origins.get(origin_overlay_lower, [])

            # Par incompleto
            if not base_geoms or not overlay_geoms:
                QgsMessageLog.logMessage(
                    f'Par incompleto para {key_field}={key_val}. '
                    f'Base ({origin_base_value}): {len(base_geoms)}, '
                    f'Analisada ({origin_overlay_value}): {len(overlay_geoms)}',
                    'GeoInterseQ', Qgis.Warning,
                )
                continue

            # 3. Unir multi-partes da mesma origem
            geom_base: QgsGeometry = base_geoms[0]
            for g in base_geoms[1:]:
                geom_base = geom_base.combine(g)
            geom_base = geom_base.makeValid()

            geom_overlay: QgsGeometry = overlay_geoms[0]
            for g in overlay_geoms[1:]:
                geom_overlay = geom_overlay.combine(g)
            geom_overlay = geom_overlay.makeValid()

            # 4. Calcular áreas individuais
            area_base_m2: float = da.measureArea(geom_base)
            area_overlay_m2: float = da.measureArea(geom_overlay)

            # 5. Calcular interseção
            inter_geom: QgsGeometry | None = geom_base.intersection(geom_overlay)
            inter_geom = inter_geom.makeValid() if inter_geom else None
            inter_area_m2: float = (
                da.measureArea(inter_geom)
                if inter_geom and not inter_geom.isEmpty()
                else 0.0
            )

            # Sem interseção espacial — registrar resultado com 0 ha / 0%
            if inter_area_m2 < 1.0:
                class_label_zero: str = key_val
                self._insert_result_row_with_class(
                    _TYPE_VECTOR, lyr.name(), class_label_zero, 0.0, 0.0,
                )
                if out_layer:
                    out_feat = QgsFeature()
                    out_feat.setAttributes([
                        _TYPE_VECTOR, lyr.name(), class_label_zero,
                        0.0, 0.0, 0.0,
                    ])
                    out_layer.dataProvider().addFeatures([out_feat])
                continue

            # 6. Validação: inter_area <= min(base, overlay)
            min_area: float = min(area_base_m2, area_overlay_m2)
            warning: bool = False
            if inter_area_m2 > min_area * 1.001:
                warning = True
                QgsMessageLog.logMessage(
                    f'AVISO — {key_field}={key_val}: '
                    f'área interseção ({inter_area_m2 / 10000:.4f} ha) > '
                    f'min(base={area_base_m2 / 10000:.4f}, '
                    f'overlay={area_overlay_m2 / 10000:.4f}) ha',
                    'GeoInterseQ', Qgis.Warning,
                )

            # 7. Calcular percentual
            denom: float = area_base_m2 if pct_relative_to_base else area_overlay_m2
            percent: float = (inter_area_m2 / denom * 100.0) if denom > 0 else 0.0

            # 8. Rótulo da classe
            class_label: str = key_val

            # 9. Inserir resultado na tabela
            self._insert_result_row_with_class(
                _TYPE_VECTOR, lyr.name(), class_label,
                inter_area_m2, percent, warning=warning,
            )

            # 10. Gravar geometria na camada de saída
            if out_layer and inter_geom and not inter_geom.isEmpty():
                out_feat = QgsFeature()
                out_feat.setGeometry(inter_geom)
                out_feat.setAttributes([
                    _TYPE_VECTOR, lyr.name(), class_label,
                    inter_area_m2, inter_area_m2 / 10000.0, percent,
                ])
                out_layer.dataProvider().addFeatures([out_feat])

    def _process_raster_layer(
        self, lyr: QgsRasterLayer, base_union: QgsGeometry, base_area_m2: float,
        crs_measure: QgsCoordinateReferenceSystem, ctx: object,
        out_layer: QgsVectorLayer | None, base_source_wkt_list: list[str] | None = None,
        base_source_crs: QgsCoordinateReferenceSystem | None = None
    ) -> None:
        """Processa a interseção espacial com uma camada raster categórica.

        Args:
            lyr (QgsRasterLayer): Camada raster de entrada.
            base_union (QgsGeometry): Geometria unificada da base (WGS84).
            base_area_m2 (float): Área total da base em m².
            crs_measure (QgsCoordinateReferenceSystem): CRS métrico de cálculo.
            ctx (object): Contexto de transformação do projeto.
            out_layer (QgsVectorLayer | None): Camada de memória de saída.
            base_source_wkt_list (list[str] | None, optional): Lista de WKT originais da base (nativo).
            base_source_crs (QgsCoordinateReferenceSystem | None, optional): CRS nativo da base.
        """
        raster_path: str = lyr.source().split('|')[0]
        try:
            ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Não foi possível abrir o raster: {e}')
            return
        if ds is None:
            QMessageBox.critical(self, 'Erro', f'Não foi possível abrir o raster:\n{raster_path}')
            return

        band = ds.GetRasterBand(1)
        nodata = band.GetNoDataValue()

        gt = ds.GetGeoTransform()
        raster_crs: QgsCoordinateReferenceSystem = lyr.crs()
        if not raster_crs.isValid():
            raster_crs_wkt: str = ds.GetProjection()
            raster_crs = QgsCoordinateReferenceSystem()
            raster_crs.createFromWkt(raster_crs_wkt)

        if gt[2] != 0 or gt[4] != 0:
            QMessageBox.warning(
                self, 'Raster rotacionado',
                f'O raster "{lyr.name()}" possui rotação no GeoTransform e não é suportado.'
            )
            ds = None
            return

        import rasterio
        import rasterio.transform
        import rasterio.windows
        from rasterio.features import rasterize as rio_rasterize
        from rasterio.transform import xy as rasterio_xy
        from shapely import wkt as shapely_wkt
        from shapely.ops import unary_union as _sh_union
        from shapely.validation import make_valid as _sh_make_valid

        shapely_geom = None
        if base_source_wkt_list and base_source_crs is not None and base_source_crs.isValid():
            try:
                tr_source_to_raster = QgsCoordinateTransform(base_source_crs, raster_crs, ctx)
                geoms_dst = []
                for w in base_source_wkt_list:
                    qg = QgsGeometry.fromWkt(w)
                    if qg.isNull() or qg.isEmpty():
                        continue
                    qg.transform(tr_source_to_raster)
                    qg = qg.makeValid()
                    sh_g = shapely_wkt.loads(qg.asWkt())
                    if sh_g is not None and not sh_g.is_empty:
                        geoms_dst.append(sh_g)

                geoms_dst = [_sh_make_valid(g) for g in geoms_dst]
                if len(geoms_dst) == 1:
                    shapely_geom = geoms_dst[0]
                elif len(geoms_dst) > 1:
                    shapely_geom = _sh_union(geoms_dst)
            except Exception:
                shapely_geom = None

        if shapely_geom is None or shapely_geom.is_empty:
            try:
                tr_to_raster = QgsCoordinateTransform(crs_measure, raster_crs, ctx)
                base_in_raster_crs = QgsGeometry(base_union)
                base_in_raster_crs.transform(tr_to_raster)
                base_in_raster_crs = base_in_raster_crs.makeValid()
                shapely_geom = shapely_wkt.loads(base_in_raster_crs.asWkt())
            except Exception as e:
                QMessageBox.critical(self, 'Erro de reprojeção', str(e))
                ds = None
                return

        if shapely_geom is None or shapely_geom.is_empty:
            ds = None
            return

        _minx, _miny, _maxx, _maxy = shapely_geom.bounds
        with rasterio.open(raster_path) as _src_rio:
            _window = rasterio.windows.from_bounds(
                _minx, _miny, _maxx, _maxy,
                transform=_src_rio.transform
            )
            src_window = _window.crop(height=_src_rio.height, width=_src_rio.width)

            if src_window.width <= 0 or src_window.height <= 0:
                QMessageBox.information(
                    self, 'Sem sobreposição',
                    f'O raster "{lyr.name()}" não cobre a extensão da camada base.'
                )
                ds = None
                return

            est_pixels: int = int(src_window.width) * int(src_window.height)
            if est_pixels > 50_000_000:
                resp = QMessageBox.question(
                    self, 'Tile grande',
                    f'O recorte do raster tem ~{est_pixels:,} pixels.\n'
                    'O cálculo pode demorar vários segundos. Continuar?',
                    QMessageBox.Yes | QMessageBox.No
                )
                if resp != QMessageBox.Yes:
                    ds = None
                    return

            data_masked = _src_rio.read(1, window=src_window, masked=True)
            window_affine = rasterio.windows.transform(src_window, _src_rio.transform)

        pixel_array: np.ndarray = np.asarray(data_masked.filled(0), dtype=np.int32)
        tile_h, tile_w = pixel_array.shape

        interior_array: np.ndarray = rio_rasterize(
            [(shapely_geom, 1)],
            out_shape=(tile_h, tile_w),
            transform=window_affine,
            fill=0,
            all_touched=False,
        ).astype(bool)

        touched_array: np.ndarray = rio_rasterize(
            [(shapely_geom, 1)],
            out_shape=(tile_h, tile_w),
            transform=window_affine,
            fill=0,
            all_touched=True,
        ).astype(bool)

        frac: np.ndarray = np.zeros(pixel_array.shape, dtype=np.float32)
        frac[interior_array] = 1.0
        frac[touched_array & ~interior_array] = 0.5

        if nodata is not None:
            nodata_mask = pixel_array == np.array(nodata, dtype=pixel_array.dtype)
            frac[nodata_mask] = 0.0

        ds = None

        if frac.sum() == 0:
            QMessageBox.information(
                self, 'Sem dados',
                f'O raster "{lyr.name()}" não possui pixels válidos dentro da camada base.'
            )
            return

        try:
            with rasterio.open(raster_path) as _src:
                _bounds = _src.bounds
                _cx: float = (_bounds.left + _bounds.right) / 2.0
                _cy: float = (_bounds.bottom + _bounds.top) / 2.0
                _zone: int = int((_cx + 180) / 6) + 1
                _utm_epsg: int = (32600 + _zone) if _cy >= 0 else (32700 + _zone)
                _tr = ProjTransformer.from_crs(
                    _src.crs, f'EPSG:{_utm_epsg}', always_xy=True
                )
                x1r, y1r = rasterio_xy(_src.transform, 0, 0, offset='ul')
                x2r, y2r = rasterio_xy(_src.transform, 1, 1, offset='ul')
                x1u, y1u = _tr.transform(x1r, y1r)
                x2u, y2u = _tr.transform(x2r, y2r)
                area_pixel_m2: float = abs(x2u - x1u) * abs(y2u - y1u)
        except Exception:
            if raster_crs.isGeographic():
                _origin_x: float = window_affine.c
                _origin_y: float = window_affine.f
                cx: float = _origin_x + (tile_w / 2.0) * gt[1]
                cy: float = _origin_y + (tile_h / 2.0) * gt[5]
                zone: int = int((cx + 180) / 6) + 1
                utm_epsg: int = (32600 + zone) if cy >= 0 else (32700 + zone)
                utm_crs = QgsCoordinateReferenceSystem(f'EPSG:{utm_epsg}')
                tr_utm = QgsCoordinateTransform(raster_crs, utm_crs, ctx)
                p0 = tr_utm.transform(QgsPointXY(cx, cy))
                p1 = tr_utm.transform(QgsPointXY(cx + gt[1], cy + gt[5]))
                area_pixel_m2 = abs(p1.x() - p0.x()) * abs(p1.y() - p0.y())
            else:
                linear_unit = raster_crs.mapUnits()
                factor: float = QgsUnitTypes.fromUnitToUnitFactor(linear_unit, QgsUnitTypes.DistanceMeters)
                area_pixel_m2 = abs(gt[1]) * abs(gt[5]) * (factor ** 2)

        # Importação das ferramentas espaciais da Shapely e rasterio
        from shapely.ops import unary_union as _sh_union_out
        from shapely.geometry import shape as _sh_shape
        from shapely.validation import make_valid as _sh_make_valid
        from shapely.ops import transform as _sh_tr_out
        from rasterio.features import shapes as rio_shapes

        # Inicializa o calculador de área geodésica do QGIS para manter coerência absoluta com o QGIS ($area)
        da = QgsDistanceArea()
        ell: str = QgsProject.instance().ellipsoid() or 'WGS84'
        da.setEllipsoid(ell)
        da.setSourceCrs(crs_measure, ctx)
        base_area_m2_ref: float = base_area_m2

        # Preparar transformador nativo para reprojetar da projeção do raster para EPSG:4326 (crs_measure)
        try:
            tr_raster_to_measure = QgsCoordinateTransform(raster_crs, crs_measure, ctx)
        except Exception:
            tr_raster_to_measure = None

        unique_vals: np.ndarray = np.unique(pixel_array[frac > 0])

        areas_por_classe_m2: dict[int, float] = {}
        geometrias_por_classe: dict[int, QgsGeometry] = {}

        for val in unique_vals:
            class_val: int = int(val)
            class_mask: np.ndarray = (touched_array & (pixel_array == class_val)).astype(np.uint8)
            
            # Vetoriza a máscara de pixels da classe atual
            try:
                polys = [
                    _sh_shape(geom)
                    for geom, v in rio_shapes(class_mask, mask=class_mask, transform=window_affine)
                    if v == 1
                ]
                if polys:
                    merged = _sh_union_out(polys)
                    # Realiza o recorte vetorial (intersection/clip) exato pela geometria do imóvel (base)
                    merged_intersect = merged.intersection(shapely_geom)
                    merged_intersect = _sh_make_valid(merged_intersect)
                    
                    if not merged_intersect.is_empty:
                        # Converte para QgsGeometry e reprojeta para o CRS de medição (EPSG:4326)
                        qgs_geom = QgsGeometry.fromWkt(merged_intersect.wkt)
                        if tr_raster_to_measure is not None and not qgs_geom.isNull() and not qgs_geom.isEmpty():
                            qgs_geom.transform(tr_raster_to_measure)
                            qgs_geom = qgs_geom.makeValid()
                        
                        # Calcula a área geodésica elipsoidal oficial alinhada com o QGIS ($area)
                        class_area_m2 = da.measureArea(qgs_geom) if not qgs_geom.isEmpty() else 0.0
                        
                        areas_por_classe_m2[class_val] = class_area_m2
                        geometrias_por_classe[class_val] = qgs_geom
            except Exception:
                # Em caso de qualquer erro na interseção, mantém o cálculo estatístico por fração como fallback
                class_area_m2 = float(frac[pixel_array == class_val].sum()) * area_pixel_m2
                if class_area_m2 > 0:
                    areas_por_classe_m2[class_val] = class_area_m2

        # Ajuste para evitar que aproximações numéricas na discretização excedam a área de referência do imóvel
        area_classes_total_m2: float = sum(areas_por_classe_m2.values())
        if area_classes_total_m2 > base_area_m2_ref * 1.0001:
            fator: float = base_area_m2_ref / area_classes_total_m2
            areas_por_classe_m2 = {k: v * fator for k, v in areas_por_classe_m2.items()}
            area_classes_total_m2 = sum(areas_por_classe_m2.values())

        class_names: dict[int, str] = {}
        try:
            renderer = lyr.renderer()
            if isinstance(renderer, QgsPalettedRasterRenderer):
                for cls in renderer.classes():
                    label: str = cls.label.strip()
                    if label and label != str(int(cls.value)):
                        class_names[int(cls.value)] = label
        except Exception:
            pass

        if not class_names:
            try:
                band_reopen = gdal.Open(raster_path, gdal.GA_ReadOnly).GetRasterBand(1)
                rat = band_reopen.GetDefaultRAT()
                if rat is not None:
                    n_cols: int = rat.GetColumnCount()
                    n_rows: int = rat.GetRowCount()
                    val_col: int = -1
                    name_col: int = -1
                    for c in range(n_cols):
                        usage = rat.GetUsageOfCol(c)
                        if usage == gdal.GFU_MinMax:
                            val_col = c
                        elif usage == gdal.GFU_Name:
                            name_col = c
                    if name_col == -1:
                        for c in range(n_cols):
                            col_name_lower: str = rat.GetNameOfCol(c).lower()
                            if 'name' in col_name_lower or 'class' in col_name_lower:
                                name_col = c
                                break
                    if val_col >= 0 and name_col >= 0:
                        for r in range(n_rows):
                            try:
                                class_names[rat.GetValueAsInt(r, val_col)] = rat.GetValueAsString(r, name_col)
                            except Exception:
                                pass
            except Exception:
                pass

        for class_val, area_m2 in areas_por_classe_m2.items():
            if class_names and class_val in class_names:
                class_label: str = f"{class_val} – {class_names[class_val]}"
            else:
                class_label = str(class_val)

            percent: float = (area_m2 / area_classes_total_m2 * 100.0) if area_classes_total_m2 > 0 else 0.0

            self._insert_result_row_with_class(_TYPE_RASTER, lyr.name(), class_label, area_m2, percent)

            if out_layer and class_val in geometrias_por_classe:
                geom_4326 = geometrias_por_classe[class_val]
                try:
                    feat = QgsFeature()
                    feat.setGeometry(geom_4326)
                    feat.setAttributes([
                        _TYPE_RASTER, lyr.name(), class_label, area_m2, area_m2 / 10000.0, percent
                    ])
                    out_layer.dataProvider().addFeatures([feat])
                except Exception:
                    feat = QgsFeature()
                    feat.setAttributes([
                        _TYPE_RASTER, lyr.name(), class_label, area_m2, area_m2 / 10000.0, percent
                    ])
                    out_layer.dataProvider().addFeatures([feat])

        if out_layer:
            try:
                renderer = lyr.renderer()
                if isinstance(renderer, QgsPalettedRasterRenderer):
                    color_map: dict[int, QColor] = {int(cls.value): cls.color for cls in renderer.classes()}
                    categories: list[QgsRendererCategory] = []
                    for class_val, area_m2 in areas_por_classe_m2.items():
                        if class_names and class_val in class_names:
                            label: str = f"{class_val} – {class_names[class_val]}"
                        else:
                            label = str(class_val)
                        color: QColor = color_map.get(class_val, QColor(128, 128, 128))
                        symbol: QgsFillSymbol = QgsFillSymbol.createSimple({
                            'color': color.name(),
                            'outline_style': 'no',
                        })
                        categories.append(QgsRendererCategory(label, symbol, label))
                    if categories:
                        out_layer.setRenderer(
                            QgsCategorizedSymbolRenderer('class', categories)
                        )
            except Exception:
                pass


class GeoInterseQPlugin:
    """Plugin QGIS para carregar a interface e as ações do GeoInterseQ."""

    def __init__(self, iface: object) -> None:
        """Inicializa o plugin com a referência da interface do QGIS.

        Args:
            iface (object): Interface principal do QGIS.
        """
        self.iface: object = iface
        self.action: QAction | None = None
        self.dialog: GeoInterseQDialog | None = None

    def initGui(self) -> None:
        """Monta o botão na barra de ferramentas e no menu correspondente do QGIS."""
        icon_path: Path = Path(__file__).parent / 'icon.png'
        icon: QIcon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
        self.action = QAction(icon, 'GeoInterseQ', self.iface.mainWindow())
        self.action.setToolTip('GeoInterseQ — área de interseção e % dentro da base')
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(PLUGIN_MENU, self.action)

    def unload(self) -> None:
        """Descarrega os widgets e as ações do plugin ao ser desativado."""
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu(PLUGIN_MENU, self.action)
        if self.dialog:
            self.dialog.close()

    def run(self) -> None:
        """Executa e exibe o diálogo principal do plugin."""
        if self.dialog is None or not self.dialog.isVisible():
            self.dialog = GeoInterseQDialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
