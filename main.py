import sys
import subprocess

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget

from core.app_info import APP_NAME, APP_VERSION, GITHUB_BRANCH, GITHUB_REPO, UPDATE_METADATA_URL
from core.auto_update import (
    UpdateCheckError,
    UpdateInstallError,
    check_for_update,
    download_update_installer,
    resolve_metadata_url,
)
from core.paths import get_resource_path
from db.database import init_db
from modules.facturacion.widget import FacturacionWidget
from modules.pagos.widget import PagosWidget
from modules.socios.widget import SociosWidget
from modules.training.widget import TrainingWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 700)

        icon_path = get_resource_path("assets", "icons", "PrimalLogo.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.socios_widget = SociosWidget()
        self.pagos_widget = PagosWidget()
        self.training_widget = TrainingWidget()
        self.facturacion_widget = FacturacionWidget()

        self.socios_widget.socios_changed.connect(self.pagos_widget.load_socios)
        self.socios_widget.socios_changed.connect(self.pagos_widget.load_payments_table)

        self.tabs.addTab(self.socios_widget, "Socios")
        self.tabs.addTab(self.pagos_widget, "Pagos")
        self.tabs.addTab(self.training_widget, "Training")
        self.tabs.addTab(self.facturacion_widget, "Facturacion")

        self._build_menu()
        QTimer.singleShot(1800, self.check_updates_silent)

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("Ayuda")

        action_check_updates = QAction("Buscar actualizaciones", self)
        action_check_updates.triggered.connect(self.check_updates_manual)
        menu.addAction(action_check_updates)

    def _check_updates(self, manual: bool) -> None:
        metadata_url = resolve_metadata_url(UPDATE_METADATA_URL, GITHUB_REPO, GITHUB_BRANCH)
        if not metadata_url:
            if manual:
                QMessageBox.information(
                    self,
                    "Actualizaciones",
                    "No hay fuente de actualizacion configurada.",
                )
            return

        try:
            update = check_for_update(APP_VERSION, metadata_url)
        except UpdateCheckError as exc:
            if manual:
                QMessageBox.warning(self, "Actualizaciones", str(exc))
            return

        if not update:
            if manual:
                QMessageBox.information(
                    self,
                    "Actualizaciones",
                    f"Ya tienes la ultima version instalada ({APP_VERSION}).",
                )
            return

        details = f"Hay una nueva version disponible: {update.version}."
        if update.notes:
            details += f"\n\nNovedades:\n{update.notes}"
        details += "\n\nQuieres descargar e instalar ahora?"

        answer = QMessageBox.question(self, "Actualizacion disponible", details)
        if answer == QMessageBox.StandardButton.Yes:
            self._run_installer_update(update.download_url, update.version)

    def _run_installer_update(self, download_url: str, version: str) -> None:
        try:
            installer_path = download_update_installer(download_url, APP_NAME, version)
        except UpdateInstallError as exc:
            QMessageBox.warning(self, "Actualizaciones", str(exc))
            return

        try:
            subprocess.Popen([str(installer_path)], shell=False)
        except OSError as exc:
            QMessageBox.warning(self, "Actualizaciones", f"No se pudo abrir el instalador: {exc}")
            return

        QMessageBox.information(
            self,
            "Actualizacion",
            "Se abrira el instalador para actualizar Primal Gestion. La aplicacion se cerrara.",
        )
        QApplication.quit()

    def check_updates_manual(self) -> None:
        self._check_updates(manual=True)

    def check_updates_silent(self) -> None:
        self._check_updates(manual=False)


def main() -> None:
    init_db()
    app = QApplication(sys.argv)

    icon_path = get_resource_path("assets", "icons", "PrimalLogo.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    app.setStyleSheet(
        """
        QWidget {
            background-color: #2f2f33;
            color: #f4f4f4;
            font-size: 13px;
        }
        QMainWindow {
            background-color: #2a2a2e;
        }
        QTabWidget::pane {
            border: 1px solid #4c4c52;
            background: #303036;
            border-radius: 8px;
            margin-top: 8px;
        }
        QTabBar::tab {
            background: #3a3a40;
            color: #f4f4f4;
            border: 1px solid #4c4c52;
            padding: 8px 14px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background: #b6222c;
            border-color: #cc2935;
            color: #ffffff;
            font-weight: 600;
        }
        QPushButton {
            background-color: #b6222c;
            color: #ffffff;
            border: 1px solid #d4343f;
            border-radius: 7px;
            padding: 7px 12px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #cf2e39;
        }
        QPushButton:pressed {
            background-color: #8d1a22;
        }
        QLineEdit, QDateEdit, QComboBox, QTextEdit {
            background-color: #404048;
            color: #ffffff;
            border: 1px solid #5a5a62;
            border-radius: 6px;
            padding: 5px 7px;
            selection-background-color: #b6222c;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #404048;
            color: #ffffff;
            border: 1px solid #5a5a62;
            border-radius: 6px;
            padding-left: 7px;
            padding-right: 26px;
            min-height: 26px;
            selection-background-color: #b6222c;
        }
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid #5a5a62;
            border-bottom: 1px solid #5a5a62;
            background-color: #b6222c;
            border-top-right-radius: 6px;
        }
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 22px;
            border-left: 1px solid #5a5a62;
            background-color: #9d2029;
            border-bottom-right-radius: 6px;
        }
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #cf2e39;
        }
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
            width: 0px;
            height: 0px;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 8px solid #ffffff;
        }
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
            width: 0px;
            height: 0px;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 8px solid #ffffff;
        }
        QTableWidget {
            background-color: #35353b;
            border: 1px solid #4d4d55;
            gridline-color: #4a4a51;
            alternate-background-color: #2f2f34;
        }
        QHeaderView::section {
            background-color: #b6222c;
            color: #ffffff;
            border: none;
            padding: 6px;
            font-weight: 700;
        }
        QLabel {
            color: #f0f0f0;
        }
        QMessageBox {
            background-color: #2f2f33;
        }
        """
    )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
