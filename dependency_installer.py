# -*- coding: utf-8 -*-
"""Módulo para verificação e instalação assistida de dependências do GeoInterseQ.

Permite instalar bibliotecas Python como rasterio e shapely diretamente pelo QGIS,
utilizando execução em segundo plano (QThread), instalação no perfil do usuário (--user)
e tentativa de recarga a quente (hot-reload) sem exigir privilégios administrativos.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import site
import subprocess
import sys
from typing import TYPE_CHECKING

from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class DependencyInstallWorker(QThread):
    """Thread em segundo plano para executar o pip install sem travar a interface do QGIS."""

    line_received: pyqtSignal = pyqtSignal(str)
    finished: pyqtSignal = pyqtSignal(bool, str)

    def __init__(self, packages: list[str], parent: QWidget | None = None) -> None:
        """Inicializa o worker de instalação.

        Args:
            packages (list[str]): Lista de pacotes a instalar via pip.
            parent (QWidget | None): Widget pai da thread.
        """
        super().__init__(parent)
        self.packages: list[str] = packages
        self._process: subprocess.Popen[str] | None = None
        self._is_cancelled: bool = False

    def run(self) -> None:
        """Executa o comando pip install em segundo plano."""
        cmd: list[str] = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--user",
            "--prefer-binary",
            "--upgrade",
            *self.packages,
        ]

        cmd_display: str = " ".join(cmd)
        self.line_received.emit(f"Executando: {cmd_display}\n")

        creationflags: int = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                bufsize=1,
            )

            if self._process.stdout:
                for line in self._process.stdout:
                    if self._is_cancelled:
                        break
                    self.line_received.emit(line.rstrip())

            self._process.wait()

            if self._is_cancelled:
                self.finished.emit(False, "Instalação cancelada pelo usuário.")
                return

            if self._process.returncode == 0:
                self.finished.emit(True, "Processo do pip finalizado com sucesso.")
            else:
                self.finished.emit(
                    False,
                    f"O pip retornou o código de erro: {self._process.returncode}",
                )

        except Exception as exc:
            self.finished.emit(False, f"Falha crítica ao executar o instalador: {exc}")
        finally:
            self._process = None

    def cancel(self) -> None:
        """Solicita o cancelamento da instalação e finaliza o subprocesso se ativo."""
        self._is_cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass


class DependencyManager:
    """Gerencia a detecção, caminhos de sistema e recarga dinâmica de bibliotecas."""

    REQUIRED_RASTER_PACKAGES: tuple[str, ...] = ("rasterio", "shapely")

    @classmethod
    def get_missing_dependencies(cls) -> list[str]:
        """Identifica quais pacotes essenciais para raster estão ausentes.

        Returns:
            list[str]: Lista de nomes de pacotes que não puderam ser importados.
        """
        cls.ensure_user_site_in_sys_path()
        missing: list[str] = []
        for pkg in cls.REQUIRED_RASTER_PACKAGES:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        return missing

    @staticmethod
    def ensure_user_site_in_sys_path() -> Path | None:
        """Garante que a pasta site-packages do perfil do usuário esteja registrada em sys.path.

        Returns:
            Path | None: Caminho do diretório de site-packages do usuário ou None caso não exista.
        """
        try:
            user_site: str = site.getusersitepackages()
            user_path: Path = Path(user_site).resolve()
            user_path_str: str = str(user_path)

            if user_path.exists() and user_path_str not in sys.path:
                sys.path.insert(0, user_path_str)
            return user_path
        except Exception:
            return None

    @classmethod
    def try_hot_reload(cls) -> tuple[bool, str]:
        """Tenta carregar dinamicamente as bibliotecas recém-instaladas nesta sessão do QGIS.

        Returns:
            tuple[bool, str]: Booleano indicando sucesso e mensagem descritiva do resultado.
        """
        cls.ensure_user_site_in_sys_path()
        importlib.invalidate_caches()

        missing: list[str] = []
        load_errors: list[str] = []

        for pkg in cls.REQUIRED_RASTER_PACKAGES:
            try:
                if pkg in sys.modules:
                    importlib.reload(sys.modules[pkg])
                else:
                    __import__(pkg)
            except Exception as exc:
                missing.append(pkg)
                load_errors.append(f"{pkg}: {exc}")

        if not missing:
            return (
                True,
                "Todas as bibliotecas necessárias foram carregadas com sucesso no QGIS.",
            )

        err_detail: str = "\n".join(load_errors)
        return (
            False,
            "Instalação finalizada, mas as extensões binárias requerem reinício do QGIS "
            f"para vinculação das DLLs nativas.\n\nDetalhes:\n{err_detail}",
        )


class DependencyInstallerDialog(QDialog):
    """Diálogo fluente para instalação e acompanhamento de dependências do GeoInterseQ."""

    def __init__(
        self,
        missing_packages: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Inicializa a interface gráfica do instalador de dependências.

        Args:
            missing_packages (list[str] | None): Lista de pacotes a instalar. Se None, detecta auto.
            parent (QWidget | None): Widget ou janela pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Instalador de Dependências — GeoInterseQ")
        self.setMinimumSize(540, 360)
        self.resize(580, 420)

        self.missing_packages: list[str] = (
            missing_packages
            if missing_packages is not None
            else DependencyManager.get_missing_dependencies()
        )
        self.worker: DependencyInstallWorker | None = None
        self.installation_succeeded: bool = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Constrói os widgets e layouts da janela inteiramente via código PyQt5."""
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # Cabeçalho
        lbl_title: QLabel = QLabel("<b>Instalação de Bibliotecas para Análise RASTER</b>")
        lbl_title.setStyleSheet("font-size: 14px; color: #1e1e1e;")
        layout.addWidget(lbl_title)

        packages_str: str = ", ".join(self.missing_packages) if self.missing_packages else "rasterio, shapely"
        lbl_desc: QLabel = QLabel(
            "O GeoInterseQ necessita das bibliotecas Python <b>"
            f"{packages_str}</b> para efetuar operações e recortes espaciais em camadas raster.<br><br>"
            "A instalação é realizada de forma automática e segura no diretório do seu perfil de usuário "
            "com a diretiva <code>--user</code>, <b>dispensando privilégios de Administrador</b>."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #424242; font-size: 11px;")
        layout.addWidget(lbl_desc)

        # Barra de Progresso
        self.progress_bar: QProgressBar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #e0e0e0; border-radius: 4px; }"
            "QProgressBar::chunk { background-color: #2E7D32; border-radius: 4px; }"
        )
        layout.addWidget(self.progress_bar)

        # Label de Status
        self.lbl_status: QLabel = QLabel("Pronto para iniciar a instalação.")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #0d47a1; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Log Console
        lbl_log_title: QLabel = QLabel("Detalhes do processo:")
        lbl_log_title.setStyleSheet("font-size: 10px; color: #616161;")
        layout.addWidget(lbl_log_title)

        self.txt_log: QTextEdit = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas", 9))
        self.txt_log.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; "
            "border: 1px solid #333333; border-radius: 4px; padding: 6px;"
        )
        layout.addWidget(self.txt_log, stretch=1)

        # Separador
        sep: QFrame = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Botões
        btn_layout: QHBoxLayout = QHBoxLayout()
        self.btn_install: QPushButton = QPushButton("Instalar Dependências")
        self.btn_install.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 16px; font-size: 12px; }"
            "QPushButton:hover { background-color: #1b5e20; }"
            "QPushButton:pressed { background-color: #0e3d13; }"
            "QPushButton:disabled { background-color: #9e9e9e; }"
        )
        self.btn_install.clicked.connect(self.start_installation)

        self.btn_close: QPushButton = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.close)

        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_install)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def start_installation(self) -> None:
        """Inicia a execução do worker de instalação do pip."""
        if not self.missing_packages:
            self.missing_packages = ["rasterio", "shapely"]

        self.btn_install.setEnabled(False)
        self.btn_close.setText("Cancelar")
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.lbl_status.setText("Baixando e instalando pacotes pelo pip... Aguarde.")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #e65100; font-size: 11px;")
        self.txt_log.clear()

        self.worker = DependencyInstallWorker(self.missing_packages, self)
        self.worker.line_received.connect(self._on_log_line)
        self.worker.finished.connect(self._on_installation_finished)
        self.worker.start()

    def _on_log_line(self, line: str) -> None:
        """Adiciona uma linha emitida pelo pip na caixa de log.

        Args:
            line (str): Linha de texto capturada do stdout/stderr do pip.
        """
        self.txt_log.append(line)
        self.txt_log.ensureCursorVisible()

    def _on_installation_finished(self, success: bool, message: str) -> None:
        """Trata o encerramento do worker de instalação.

        Args:
            success (bool): Verdadeiro se o pip retornou código 0.
            message (str): Descrição do encerramento.
        """
        self.progress_bar.setRange(0, 100)
        self.btn_close.setText("Fechar")

        if not success:
            self.progress_bar.setValue(0)
            self.btn_install.setEnabled(True)
            self.btn_install.setText("Tentar Novamente")
            self.lbl_status.setText("Falha na instalação das dependências.")
            self.lbl_status.setStyleSheet("font-weight: bold; color: #b71c1c; font-size: 11px;")
            self.txt_log.append(f"\n[ERRO] {message}")
            return

        self.progress_bar.setValue(100)
        self.txt_log.append(f"\n[SUCESSO] {message}\nVerificando carregamento a quente das bibliotecas...")

        hot_reload_ok, reload_msg = DependencyManager.try_hot_reload()
        if hot_reload_ok:
            self.installation_succeeded = True
            self.lbl_status.setText("Instalação concluída com sucesso! Análise raster habilitada.")
            self.lbl_status.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 11px;")
            self.txt_log.append(f"[HOT-RELOAD] {reload_msg}")
            self.btn_install.setEnabled(False)
            self.btn_install.setText("Instalado")
            QMessageBox.information(
                self,
                "GeoInterseQ — Sucesso",
                "As bibliotecas foram instaladas e integradas à sua sessão atual do QGIS.\n\n"
                "A análise de camadas RASTER já está habilitada!",
            )
        else:
            self.installation_succeeded = True
            self.lbl_status.setText("Instalação concluída! Reinicie o QGIS para ativar o suporte a raster.")
            self.lbl_status.setStyleSheet("font-weight: bold; color: #0277bd; font-size: 11px;")
            self.txt_log.append(f"[AVISO] {reload_msg}")
            self.btn_install.setEnabled(False)
            self.btn_install.setText("Instalado (Requer Reinício)")
            QMessageBox.information(
                self,
                "GeoInterseQ — Reinício Recomendado",
                "As bibliotecas foram instaladas com sucesso no seu perfil.\n\n"
                "Para concluir a ativação dos módulos nativos de raster, por favor "
                "reinicie o QGIS.",
            )

    def closeEvent(self, event: object) -> None:
        """Garante o cancelamento da thread ao fechar a janela.

        Args:
            event (object): Evento de fechamento da janela.
        """
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        super().closeEvent(event)


def prompt_install_if_needed(parent: QWidget | None = None) -> bool:
    """Verifica se faltam dependências para raster e convida amigavelmente o usuário a instalar.

    Args:
        parent (QWidget | None): Janela pai para posicionamento dos diálogos.

    Returns:
        bool: True se todas as dependências estão prontas para uso, False se ainda faltarem.
    """
    missing: list[str] = DependencyManager.get_missing_dependencies()
    if not missing:
        return True

    msg: str = (
        "O GeoInterseQ identificou que as bibliotecas necessárias para análise RASTER "
        f"({', '.join(missing)}) ainda não estão instaladas no seu ambiente QGIS.\n\n"
        "Deseja instalá-las agora automaticamente com 1 clique?\n"
        "(A instalação será feita no seu perfil de usuário, sem exigir senha de administrador).\n\n"
        "Se optar por 'Não', a análise puramente vetorial continuará funcionando normalmente."
    )

    reply = QMessageBox.question(
        parent,
        "GeoInterseQ — Análise Raster",
        msg,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )

    if reply == QMessageBox.Yes:
        dlg: DependencyInstallerDialog = DependencyInstallerDialog(missing, parent)
        dlg.exec_()
        return dlg.installation_succeeded

    return False
