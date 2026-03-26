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
        self._suppress_socio_warning = False
        self._build_ui()
        self.cleanup_old_overdue_payments()
        self.load_socios()
        self.load_payments_table()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        form = QFormLayout()
        self.socio_combo = QComboBox()
        self.socio_combo.activated.connect(self._warn_if_selected_socio_overdue)
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

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar alumno:"))
        self.search_input = QComboBox()
        self.search_input.setEditable(True)
        self.search_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.search_input.setPlaceholderText("Nombre del alumno")
        self.search_input.lineEdit().textChanged.connect(self.load_payments_table)
        search_row.addWidget(self.search_input)
        root.addLayout(search_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filtrar por estado:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Al dia", "Proximos a vencerse", "Vencidos"])
        self.filter_combo.currentIndexChanged.connect(self.load_payments_table)
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        root.addLayout(filter_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Nombre y apellido", "Monto", "Fecha de pago", "Fecha proximo pago", "Estado"]
        )
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        header.setSectionResizeMode(1, header.ResizeMode.Fixed)
        header.setSectionResizeMode(2, header.ResizeMode.Fixed)
        header.setSectionResizeMode(3, header.ResizeMode.Fixed)
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 170)
        self.table.setColumnWidth(4, 120)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table)

    def load_socios(self) -> None:
        self._suppress_socio_warning = True
        current_data = self.socio_combo.currentData()
        self.socio_combo.clear()
        current_search = self.search_input.currentText().strip()
        self.search_input.clear()

        with SessionLocal() as session:
            socios = (
                session.query(Socio)
                .filter(Socio.activo.is_(True))
                .order_by(Socio.nombre_apellido.asc())
                .all()
            )

        for socio in socios:
            self.socio_combo.addItem(socio.nombre_apellido, socio.id)
            self.search_input.addItem(socio.nombre_apellido)

        if current_search:
            self.search_input.setCurrentText(current_search)

        if current_data is not None:
            idx = self.socio_combo.findData(current_data)
            if idx >= 0:
                self.socio_combo.setCurrentIndex(idx)

        self._suppress_socio_warning = False

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

        self.cleanup_old_overdue_payments()
        self.load_payments_table()

    def cleanup_old_overdue_payments(self) -> None:
        cutoff = date.today() - timedelta(days=60)
        with SessionLocal() as session:
            (
                session.query(Pago)
                .filter(Pago.fecha_proximo_pago < cutoff)
                .delete(synchronize_session=False)
            )
            session.commit()

    def load_payments_table(self) -> None:
        self.cleanup_old_overdue_payments()

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
        search_text = self.search_input.currentText().strip().lower()

        filtered_rows: list[tuple[Pago, Socio, str]] = []
        for pago, socio in rows:
            status = self._compute_status(pago.fecha_proximo_pago, today, upcoming_limit)
            if search_text and search_text not in socio.nombre_apellido.lower():
                continue
            if selected_filter == "Al dia" and status != "Al dia":
                continue
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

        # Keep stable fixed widths even when there are no rows loaded.
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 170)
        self.table.setColumnWidth(4, 120)

    @staticmethod
    def _compute_status(next_payment: date, today: date, upcoming_limit: date) -> str:
        if next_payment < today:
            return "Vencido"
        if today <= next_payment <= upcoming_limit:
            return "Proximo a vencer"
        return "Al dia"

    def _warn_if_selected_socio_overdue(self, _index: int | None = None) -> None:
        if self._suppress_socio_warning:
            return

        socio_id = self.socio_combo.currentData()
        if socio_id is None:
            return

        with SessionLocal() as session:
            last_payment = (
                session.query(Pago)
                .filter(Pago.socio_id == int(socio_id))
                .order_by(Pago.fecha_proximo_pago.desc(), Pago.fecha_pago.desc(), Pago.id.desc())
                .first()
            )

        if not last_payment:
            return

        today = date.today()
        if last_payment.fecha_proximo_pago < today:
            QMessageBox.warning(self, "Alerta", "El alumno adeuda mensualidad")
