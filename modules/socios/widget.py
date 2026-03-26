from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from PyQt6.QtCore import QDate, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDateEdit,
    QSizePolicy,
)

try:
    from PyQt6.QtPdf import QPdfDocument
    from PyQt6.QtPdfWidgets import QPdfView

    PDF_PREVIEW_AVAILABLE = True
except ImportError:
    QPdfDocument = None
    QPdfView = None
    PDF_PREVIEW_AVAILABLE = False

from db.database import SessionLocal
from db.models import Socio
from core.paths import get_medical_files_dir, get_resource_path


class SociosWidget(QWidget):
    socios_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.current_socio_id: int | None = None
        self.selected_medical_file: str | None = None
        self._build_ui()
        self.load_socios()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar alumno:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre o telefono")
        self.search_input.textChanged.connect(self.filter_socios_table)
        search_row.addWidget(self.search_input)
        left_panel.addLayout(search_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre y apellido", "Nacimiento", "Telefono", "Planilla medica"]
        )
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.Fixed)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setSectionResizeMode(2, header.ResizeMode.Fixed)
        header.setSectionResizeMode(3, header.ResizeMode.Fixed)
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 170)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_selection)
        left_panel.addWidget(self.table)
        layout.addLayout(left_panel, 2)

        right_panel = QVBoxLayout()
        form = QFormLayout()

        self.nombre_input = QLineEdit()
        self.fecha_nacimiento_input = QDateEdit()
        self.fecha_nacimiento_input.setCalendarPopup(True)
        self.fecha_nacimiento_input.setDate(QDate.currentDate().addYears(-18))

        self.telefono_input = QLineEdit()
        self.planilla_input = QLineEdit()
        self.planilla_input.setReadOnly(True)

        planilla_layout = QHBoxLayout()
        planilla_layout.addWidget(self.planilla_input)
        browse_btn = QPushButton("Subir planilla")
        browse_btn.clicked.connect(self.select_medical_file)
        planilla_layout.addWidget(browse_btn)

        form.addRow("Nombre y apellido:", self.nombre_input)
        form.addRow("Fecha de nacimiento:", self.fecha_nacimiento_input)
        form.addRow("Numero de telefono:", self.telefono_input)
        form.addRow("Planilla medica (opcional):", planilla_layout)

        right_panel.addLayout(form)

        btn_layout = QHBoxLayout()
        nuevo_btn = QPushButton("Nuevo")
        guardar_btn = QPushButton("Guardar")
        eliminar_btn = QPushButton("Eliminar")
        revisar_btn = QPushButton("Revisar datos")

        nuevo_btn.clicked.connect(self.clear_form)
        guardar_btn.clicked.connect(self.save_socio)
        eliminar_btn.clicked.connect(self.delete_socio)
        revisar_btn.clicked.connect(self.review_selected_socio)

        btn_layout.addWidget(nuevo_btn)
        btn_layout.addWidget(guardar_btn)
        btn_layout.addWidget(eliminar_btn)
        btn_layout.addWidget(revisar_btn)

        right_panel.addLayout(btn_layout)
        right_panel.addWidget(QLabel("Completa los datos y guarda para crear o editar un alumno."))

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        logo_path = get_resource_path("assets", "icons", "PrimalLogo.png")
        logo_pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if logo_pixmap.isNull():
            self.logo_label.setText("PRIMAL")
        else:
            self.logo_label.setPixmap(
                logo_pixmap.scaled(420, 420, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        right_panel.addWidget(self.logo_label, 1)

        developed_by_label = QLabel("Desarrollado por")
        developed_by_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(developed_by_label)

        self.vexus_logo_label = QLabel()
        self.vexus_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vexus_logo_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        vexus_logo_path = get_resource_path("assets", "icons", "Logo_vexus.png")
        vexus_pixmap = QPixmap(str(vexus_logo_path)) if vexus_logo_path.exists() else QPixmap()
        if vexus_pixmap.isNull():
            self.vexus_logo_label.setText("Vexus")
        else:
            self.vexus_logo_label.setPixmap(
                vexus_pixmap.scaled(150, 46, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        self.vexus_logo_label.mousePressEvent = self._open_vexus_site
        right_panel.addWidget(self.vexus_logo_label)

        layout.addLayout(right_panel, 1)

    def _open_vexus_site(self, _event) -> None:
        QDesktopServices.openUrl(QUrl("https://www.grupovexus.com"))

    def load_socios(self) -> None:
        with SessionLocal() as session:
            socios = session.query(Socio).order_by(Socio.id.asc()).all()

        self.table.setRowCount(len(socios))
        for row, socio in enumerate(socios):
            self.table.setItem(row, 0, QTableWidgetItem(str(socio.id)))
            self.table.setItem(row, 1, QTableWidgetItem(socio.nombre_apellido))
            self.table.setItem(row, 2, QTableWidgetItem(socio.fecha_nacimiento.strftime("%Y-%m-%d")))
            self.table.setItem(row, 3, QTableWidgetItem(socio.telefono))
            planilla_estado = "Cargada" if socio.planilla_medica_path else "Sin planilla"
            self.table.setItem(row, 4, QTableWidgetItem(planilla_estado))

        # Keep stable widths even when the table has many rows.
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 170)
        self.filter_socios_table(self.search_input.text())

    def filter_socios_table(self, query: str) -> None:
        text = query.strip().lower()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            phone_item = self.table.item(row, 3)

            haystack = ""
            if name_item:
                haystack += name_item.text().lower()
            if phone_item:
                haystack += f" {phone_item.text().lower()}"

            should_hide = bool(text) and text not in haystack
            self.table.setRowHidden(row, should_hide)

    def on_table_selection(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        self.current_socio_id = int(self.table.item(row, 0).text())

        with SessionLocal() as session:
            socio = session.get(Socio, self.current_socio_id)

        if not socio:
            return

        self.nombre_input.setText(socio.nombre_apellido)
        self.fecha_nacimiento_input.setDate(QDate(socio.fecha_nacimiento.year, socio.fecha_nacimiento.month, socio.fecha_nacimiento.day))
        self.telefono_input.setText(socio.telefono)
        self.selected_medical_file = socio.planilla_medica_path
        self.planilla_input.setText(Path(socio.planilla_medica_path).name if socio.planilla_medica_path else "")

    def clear_form(self) -> None:
        self.current_socio_id = None
        self.selected_medical_file = None
        self.nombre_input.clear()
        self.fecha_nacimiento_input.setDate(QDate.currentDate().addYears(-18))
        self.telefono_input.clear()
        self.planilla_input.clear()
        self.table.clearSelection()

    def select_medical_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar planilla medica",
            "",
            "Archivos PDF o Imagen (*.pdf *.png *.jpg *.jpeg)",
        )
        if file_path:
            self.selected_medical_file = file_path
            self.planilla_input.setText(Path(file_path).name)

    def _store_medical_file(self, selected_path: str) -> str:
        source = Path(selected_path)
        medical_dir = get_medical_files_dir()
        medical_dir.mkdir(parents=True, exist_ok=True)

        target_name = f"{date.today().strftime('%Y%m%d')}_{source.name}"
        target = medical_dir / target_name

        if source.resolve() != target.resolve():
            shutil.copy2(source, target)

        return str(target)

    def save_socio(self) -> None:
        nombre = self.nombre_input.text().strip()
        telefono = self.telefono_input.text().strip()
        nacimiento = self.fecha_nacimiento_input.date().toPyDate()
        planilla = self.selected_medical_file

        if not nombre or not telefono:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y telefono son obligatorios.")
            return

        stored_planilla: str | None = None
        if planilla:
            try:
                planilla_path = Path(planilla)
                if planilla_path.exists():
                    stored_planilla = self._store_medical_file(planilla)
                else:
                    # Keep existing relative/absolute stored path if file already belongs to the app.
                    stored_planilla = planilla
            except OSError as exc:
                QMessageBox.critical(self, "Error", f"No se pudo guardar la planilla: {exc}")
                return

        with SessionLocal() as session:
            if self.current_socio_id is None:
                socio = Socio(
                    nombre_apellido=nombre,
                    fecha_nacimiento=nacimiento,
                    telefono=telefono,
                    planilla_medica_path=stored_planilla,
                    activo=True,
                )
                session.add(socio)
            else:
                socio = session.get(Socio, self.current_socio_id)
                if not socio:
                    QMessageBox.warning(self, "No encontrado", "El socio seleccionado no existe.")
                    return
                socio.nombre_apellido = nombre
                socio.fecha_nacimiento = nacimiento
                socio.telefono = telefono
                socio.planilla_medica_path = stored_planilla

            session.commit()

        self.load_socios()
        self.clear_form()
        self.socios_changed.emit()

    def review_selected_socio(self) -> None:
        if self.current_socio_id is None:
            QMessageBox.information(self, "Seleccion requerida", "Selecciona un socio para revisar sus datos.")
            return

        with SessionLocal() as session:
            socio = session.get(Socio, self.current_socio_id)

        if not socio:
            QMessageBox.warning(self, "No encontrado", "El socio seleccionado no existe.")
            return

        dialog = SocioDetailDialog(socio, self)
        dialog.exec()

    def delete_socio(self) -> None:
        if self.current_socio_id is None:
            QMessageBox.information(self, "Seleccion requerida", "Selecciona un socio para eliminar.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "Se eliminara el socio y sus pagos. Continuar?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            socio = session.get(Socio, self.current_socio_id)
            if not socio:
                QMessageBox.warning(self, "No encontrado", "El socio seleccionado ya no existe.")
                return
            session.delete(socio)
            session.commit()

        self.load_socios()
        self.clear_form()
        self.socios_changed.emit()


class SocioDetailDialog(QDialog):
    def __init__(self, socio: Socio, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.socio = socio
        self._pdf_document = None
        self.setWindowTitle("Revisar datos del alumno")
        self.resize(1000, 700)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        info = QFormLayout()
        info.addRow("Nombre y apellido:", QLabel(self.socio.nombre_apellido))
        info.addRow("Fecha de nacimiento:", QLabel(self.socio.fecha_nacimiento.strftime("%Y-%m-%d")))
        info.addRow("Numero de telefono:", QLabel(self.socio.telefono))
        info.addRow(
            "Planilla medica:",
            QLabel("Cargada" if self.socio.planilla_medica_path else "Sin planilla"),
        )
        root.addLayout(info)

        root.addWidget(QLabel("Vista de planilla medica"))
        root.addWidget(self._build_medical_preview())

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        root.addLayout(close_row)

    def _build_medical_preview(self) -> QWidget:
        planilla_path = self.socio.planilla_medica_path
        if not planilla_path:
            return QLabel("Este alumno no tiene planilla medica cargada.")

        path = Path(planilla_path)
        if not path.exists():
            return QLabel("No se encontro el archivo de planilla medica.")

        extension = path.suffix.lower()
        if extension in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                return QLabel("No se pudo cargar la imagen de la planilla medica.")

            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(False)
            image_label.setMinimumSize(700, 500)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(image_label)
            return scroll

        if extension == ".pdf" and PDF_PREVIEW_AVAILABLE and QPdfDocument and QPdfView:
            self._pdf_document = QPdfDocument(self)
            self._pdf_document.load(str(path))

            pdf_view = QPdfView(self)
            pdf_view.setDocument(self._pdf_document)
            pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            return pdf_view

        fallback = QWidget()
        layout = QVBoxLayout(fallback)
        layout.addWidget(QLabel("No hay visor integrado disponible para este tipo de archivo."))
        open_btn = QPushButton("Abrir archivo")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))))
        layout.addWidget(open_btn)
        layout.addStretch()
        return fallback
