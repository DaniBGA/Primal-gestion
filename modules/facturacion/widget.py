from __future__ import annotations

from calendar import month_name
from datetime import date, datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import extract, func

from core.paths import get_desktop_dir
from db.database import SessionLocal
from db.models import Pago, Socio


class FacturacionWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._rows_months: list[tuple[int, int]] = []
        self._build_ui()
        self.load_facturacion()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Mes:"))
        self.month_combo = QComboBox()
        self.month_combo.addItem("Todos", 0)
        for month in range(1, 13):
            self.month_combo.addItem(month_name[month].capitalize(), month)
        self.month_combo.currentIndexChanged.connect(self.load_facturacion)
        filters.addWidget(self.month_combo)

        filters.addWidget(QLabel("Ano:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(date.today().year)
        self.year_spin.valueChanged.connect(self.load_facturacion)
        filters.addWidget(self.year_spin)

        reload_btn = QPushButton("Actualizar")
        reload_btn.clicked.connect(self.load_facturacion)
        filters.addWidget(reload_btn)
        filters.addStretch()

        root.addLayout(filters)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Resumen", "Mas info"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, self.table.horizontalHeader().ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        root.addWidget(self.table)

    def load_facturacion(self) -> None:
        year = int(self.year_spin.value())
        month = int(self.month_combo.currentData())

        with SessionLocal() as session:
            query = (
                session.query(
                    extract("year", Pago.fecha_pago).label("year"),
                    extract("month", Pago.fecha_pago).label("month"),
                    func.sum(Pago.monto).label("total"),
                )
                .filter(extract("year", Pago.fecha_pago) == year)
            )

            if month:
                query = query.filter(extract("month", Pago.fecha_pago) == month)

            rows = (
                query.group_by(
                    extract("year", Pago.fecha_pago),
                    extract("month", Pago.fecha_pago),
                )
                .order_by(extract("month", Pago.fecha_pago))
                .all()
            )

        self._rows_months = [(int(row.year), int(row.month)) for row in rows]
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            month_number = int(row.month)
            year_number = int(row.year)
            total = float(row.total or 0.0)
            month_label = month_name[month_number].capitalize()
            summary = f"Facturacion de {month_label} {year_number}: $ {total:,.2f}"

            self.table.setItem(row_idx, 0, QTableWidgetItem(summary))

            details_btn = QPushButton("Mas info")
            details_btn.clicked.connect(
                lambda _checked=False, y=year_number, m=month_number: self.generate_month_report(y, m)
            )
            self.table.setCellWidget(row_idx, 1, details_btn)

        if not rows:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("Sin datos para el filtro seleccionado."))
            self.table.setItem(0, 1, QTableWidgetItem("-"))

    def generate_month_report(self, year: int, month: int) -> None:
        with SessionLocal() as session:
            detail_rows = (
                session.query(
                    Socio.nombre_apellido,
                    func.count(Pago.id).label("cuotas_pagadas"),
                    func.sum(Pago.monto).label("monto_total"),
                )
                .join(Pago, Pago.socio_id == Socio.id)
                .filter(extract("year", Pago.fecha_pago) == year)
                .filter(extract("month", Pago.fecha_pago) == month)
                .group_by(Socio.nombre_apellido)
                .order_by(Socio.nombre_apellido.asc())
                .all()
            )

            month_total = (
                session.query(func.sum(Pago.monto))
                .filter(extract("year", Pago.fecha_pago) == year)
                .filter(extract("month", Pago.fecha_pago) == month)
                .scalar()
            )

        if not detail_rows:
            QMessageBox.information(self, "Sin datos", "No hay pagos para ese mes y ano.")
            return

        reports_dir = get_desktop_dir()
        month_label = month_name[month].capitalize()
        file_path = reports_dir / f"facturacion_{year}_{month:02d}.pdf"

        try:
            self._write_pdf(file_path, year, month_label, detail_rows, float(month_total or 0.0))
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {exc}")
            return

        QMessageBox.information(
            self,
            "PDF generado",
            f"Reporte creado en:\n{file_path}",
        )

    @staticmethod
    def _write_pdf(
        file_path: Path,
        year: int,
        month_label: str,
        detail_rows: list,
        month_total: float,
    ) -> None:
        pdf = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4

        y = height - 50
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, y, f"Facturacion - {month_label} {year}")

        y -= 30
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        y -= 30
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y, "Alumno")
        pdf.drawString(300, y, "Cuotas pagadas")
        pdf.drawString(430, y, "Monto total")

        y -= 15
        pdf.line(40, y, width - 40, y)
        y -= 18

        pdf.setFont("Helvetica", 10)
        for nombre, cuotas, monto in detail_rows:
            if y < 80:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)

            pdf.drawString(40, y, str(nombre))
            pdf.drawRightString(390, y, str(int(cuotas or 0)))
            pdf.drawRightString(550, y, f"$ {float(monto or 0.0):,.2f}")
            y -= 18

        y -= 8
        pdf.line(40, y, width - 40, y)
        y -= 22
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Total del mes")
        pdf.drawRightString(550, y, f"$ {month_total:,.2f}")

        pdf.save()
