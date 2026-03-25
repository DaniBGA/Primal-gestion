from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import and_, func

from db.database import SessionLocal
from db.models import Pago, Socio


class PagosWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()
        self.load_socios()
        self.load_payments_table()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        form = QFormLayout()
        self.socio_combo = QComboBox()
        self.monto_input = QDoubleSpinBox()
        self.monto_input.setMaximum(1_000_000)
        self.monto_input.setPrefix("$ ")
        self.monto_input.setDecimals(2)
        self.monto_input.setValue(10000)

        self.fecha_pago_input = QDateEdit()
        self.fecha_pago_input.setCalendarPopup(True)
        self.fecha_pago_input.setDate(QDate.currentDate())

        self.fecha_proximo_input = QDateEdit()
        self.fecha_proximo_input.setCalendarPopup(True)
        self.fecha_proximo_input.setDate(QDate.currentDate().addDays(30))

        form.addRow("Alumno:", self.socio_combo)
        form.addRow("Monto:", self.monto_input)
        form.addRow("Fecha de pago:", self.fecha_pago_input)
        form.addRow("Fecha proximo pago:", self.fecha_proximo_input)

        root.addLayout(form)

        action_row = QHBoxLayout()
        save_btn = QPushButton("Registrar pago")
        save_btn.clicked.connect(self.register_payment)
        action_row.addWidget(save_btn)
        action_row.addStretch()
        root.addLayout(action_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filtrar por estado:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Proximos a vencerse", "Vencidos"])
        self.filter_combo.currentIndexChanged.connect(self.load_payments_table)
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        root.addLayout(filter_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Nombre y apellido", "Monto", "Fecha de pago", "Fecha proximo pago", "Estado"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table)

    def load_socios(self) -> None:
        current_data = self.socio_combo.currentData()
        self.socio_combo.clear()

        with SessionLocal() as session:
            socios = (
                session.query(Socio)
                .filter(Socio.activo.is_(True))
                .order_by(Socio.nombre_apellido.asc())
                .all()
            )

        for socio in socios:
            self.socio_combo.addItem(socio.nombre_apellido, socio.id)

        if current_data is not None:
            idx = self.socio_combo.findData(current_data)
            if idx >= 0:
                self.socio_combo.setCurrentIndex(idx)

    def register_payment(self) -> None:
        socio_id = self.socio_combo.currentData()
        if socio_id is None:
            QMessageBox.warning(self, "Sin alumnos", "Primero crea un alumno en la pestana Socios.")
            return

        fecha_pago = self.fecha_pago_input.date().toPyDate()
        fecha_proximo = self.fecha_proximo_input.date().toPyDate()

        if fecha_proximo <= fecha_pago:
            QMessageBox.warning(
                self,
                "Fechas invalidas",
                "La fecha de proximo pago debe ser mayor que la fecha de pago.",
            )
            return

        pago = Pago(
            socio_id=int(socio_id),
            monto=float(self.monto_input.value()),
            fecha_pago=fecha_pago,
            fecha_proximo_pago=fecha_proximo,
        )

        with SessionLocal() as session:
            session.add(pago)
            session.commit()

        self.load_payments_table()

    def load_payments_table(self) -> None:
        with SessionLocal() as session:
            latest_payment_subquery = (
                session.query(
                    Pago.socio_id.label("socio_id"),
                    func.max(Pago.fecha_pago).label("max_fecha_pago"),
                )
                .group_by(Pago.socio_id)
                .subquery()
            )

            rows = (
                session.query(Pago, Socio)
                .join(
                    latest_payment_subquery,
                    and_(
                        Pago.socio_id == latest_payment_subquery.c.socio_id,
                        Pago.fecha_pago == latest_payment_subquery.c.max_fecha_pago,
                    ),
                )
                .join(Socio, Socio.id == Pago.socio_id)
                .order_by(Pago.fecha_proximo_pago.asc())
                .all()
            )

        today = date.today()
        upcoming_limit = today + timedelta(days=7)
        selected_filter = self.filter_combo.currentText()

        filtered_rows: list[tuple[Pago, Socio, str]] = []
        for pago, socio in rows:
            status = self._compute_status(pago.fecha_proximo_pago, today, upcoming_limit)
            if selected_filter == "Proximos a vencerse" and status != "Proximo a vencer":
                continue
            if selected_filter == "Vencidos" and status != "Vencido":
                continue
            filtered_rows.append((pago, socio, status))

        self.table.setRowCount(len(filtered_rows))
        for row_idx, (pago, socio, status) in enumerate(filtered_rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(socio.nombre_apellido))
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"$ {pago.monto:,.2f}"))
            self.table.setItem(row_idx, 2, QTableWidgetItem(pago.fecha_pago.strftime("%Y-%m-%d")))
            self.table.setItem(
                row_idx,
                3,
                QTableWidgetItem(pago.fecha_proximo_pago.strftime("%Y-%m-%d")),
            )
            self.table.setItem(row_idx, 4, QTableWidgetItem(status))

        self.table.resizeColumnsToContents()

    @staticmethod
    def _compute_status(next_payment: date, today: date, upcoming_limit: date) -> str:
        if next_payment < today:
            return "Vencido"
        if today <= next_payment <= upcoming_limit:
            return "Proximo a vencer"
        return "Al dia"
