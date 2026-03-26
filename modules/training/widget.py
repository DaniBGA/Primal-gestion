from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from db.database import SessionLocal
from db.models import Ejercicio, SesionEntrenamiento
from core.paths import get_resource_path


class TrainingWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self._start_delay_timer = QTimer(self)
        self._start_delay_timer.setSingleShot(True)
        self._start_delay_timer.timeout.connect(self._begin_countdown_after_delay)

        self.exercise_seconds = 0
        self.rest_seconds = 0
        self.total_rounds = 1
        self.current_round = 1
        self.is_rest_phase = False
        self.remaining_seconds = 0
        self.current_exercise_id: int | None = None
        self.session_start: datetime | None = None
        self._countdown_sound_played = False
        self._pending_start = False

        self._start_audio_output = QAudioOutput(self)
        self._start_player = QMediaPlayer(self)
        self._start_player.setAudioOutput(self._start_audio_output)

        self._countdown_audio_output = QAudioOutput(self)
        self._countdown_player = QMediaPlayer(self)
        self._countdown_player.setAudioOutput(self._countdown_audio_output)

        self._configure_sounds()

        self._build_ui()
        self.load_exercises()

    def _configure_sounds(self) -> None:
        start_sound = get_resource_path("assets", "sounds", "Air Horn Sound Effect.mp3")
        countdown_sound = get_resource_path(
            "assets",
            "sounds",
            "3 Seconds Timer #shorts #youtubeshorts #countdown.mp3",
        )

        if start_sound.exists():
            self._start_player.setSource(QUrl.fromLocalFile(str(start_sound)))
        if countdown_sound.exists():
            self._countdown_player.setSource(QUrl.fromLocalFile(str(countdown_sound)))

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        create_box = QFormLayout()
        self.exercise_name_input = QLineEdit()
        self.exercise_duration_input = QSpinBox()
        self.exercise_duration_input.setRange(5, 7200)
        self.exercise_duration_input.setValue(180)
        self.rest_duration_input = QSpinBox()
        self.rest_duration_input.setRange(0, 600)
        self.rest_duration_input.setValue(30)
        self.rounds_input = QSpinBox()
        self.rounds_input.setRange(1, 50)
        self.rounds_input.setValue(3)
        self.exercise_desc_input = QTextEdit()
        self.exercise_desc_input.setPlaceholderText("Descripcion opcional")
        self.exercise_desc_input.setFixedHeight(70)

        create_box.addRow("Nuevo ejercicio:", self.exercise_name_input)
        create_box.addRow("Duracion (segundos):", self.exercise_duration_input)
        create_box.addRow("Descanso (segundos):", self.rest_duration_input)
        create_box.addRow("Rondas:", self.rounds_input)
        create_box.addRow("Descripcion:", self.exercise_desc_input)
        root.addLayout(create_box)

        create_btn = QPushButton("Crear ejercicio")
        create_btn.clicked.connect(self.create_exercise)
        create_row = QHBoxLayout()
        create_row.addWidget(create_btn)
        edit_btn = QPushButton("Editar ejercicio")
        edit_btn.clicked.connect(self.edit_exercise)
        create_row.addWidget(edit_btn)
        delete_btn = QPushButton("Borrar entrenamiento")
        delete_btn.clicked.connect(self.delete_exercise)
        create_row.addWidget(delete_btn)
        create_row.addStretch()
        root.addLayout(create_row)

        select_row = QHBoxLayout()
        self.exercise_combo = QComboBox()
        self.exercise_combo.currentIndexChanged.connect(self.on_exercise_selected)
        select_row.addWidget(QLabel("Elegir ejercicio:"))
        select_row.addWidget(self.exercise_combo)
        root.addLayout(select_row)

        root.addWidget(QLabel("Descripcion del entrenamiento seleccionado:"))
        self.selected_desc = QTextEdit()
        self.selected_desc.setReadOnly(True)
        self.selected_desc.setFixedHeight(90)
        self.selected_desc.setPlaceholderText("Sin descripcion")
        root.addWidget(self.selected_desc)

        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self.timer_label)

        self.phase_label = QLabel("Sin ejercicio")
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.phase_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        root.addWidget(self.phase_label)

        controls = QHBoxLayout()
        start_btn = QPushButton("Iniciar")
        pause_btn = QPushButton("Pausar")
        reset_btn = QPushButton("Reiniciar")

        start_btn.clicked.connect(self.start_timer)
        pause_btn.clicked.connect(self.pause_timer)
        reset_btn.clicked.connect(self.reset_timer)

        controls.addWidget(start_btn)
        controls.addWidget(pause_btn)
        controls.addWidget(reset_btn)
        root.addLayout(controls)

        root.addStretch()

    def create_exercise(self) -> None:
        nombre = self.exercise_name_input.text().strip()
        duracion = int(self.exercise_duration_input.value())
        descanso = int(self.rest_duration_input.value())
        rondas = int(self.rounds_input.value())
        descripcion = self.exercise_desc_input.toPlainText().strip() or None

        if not nombre:
            QMessageBox.warning(self, "Dato requerido", "Ingresa el nombre del ejercicio.")
            return

        with SessionLocal() as session:
            exists = session.query(Ejercicio).filter(Ejercicio.nombre == nombre).first()
            if exists:
                QMessageBox.warning(self, "Duplicado", "Ya existe un ejercicio con ese nombre.")
                return

            ejercicio = Ejercicio(
                nombre=nombre,
                duracion_segundos=duracion,
                descanso_segundos=descanso,
                rondas=rondas,
                descripcion=descripcion,
            )
            session.add(ejercicio)
            session.commit()

        self.exercise_name_input.clear()
        self.exercise_desc_input.clear()
        self.exercise_duration_input.setValue(180)
        self.rest_duration_input.setValue(30)
        self.rounds_input.setValue(3)
        self.load_exercises()

    def edit_exercise(self) -> None:
        exercise_id = self.exercise_combo.currentData()
        if exercise_id is None:
            QMessageBox.information(self, "Sin seleccion", "Selecciona un entrenamiento para editar.")
            return

        nombre = self.exercise_name_input.text().strip()
        duracion = int(self.exercise_duration_input.value())
        descanso = int(self.rest_duration_input.value())
        rondas = int(self.rounds_input.value())
        descripcion = self.exercise_desc_input.toPlainText().strip() or None

        if not nombre:
            QMessageBox.warning(self, "Dato requerido", "Ingresa el nombre del ejercicio.")
            return

        with SessionLocal() as session:
            exercise = session.get(Ejercicio, int(exercise_id))
            if not exercise:
                QMessageBox.warning(self, "No encontrado", "El entrenamiento ya no existe.")
                return

            duplicate = (
                session.query(Ejercicio)
                .filter(Ejercicio.nombre == nombre, Ejercicio.id != int(exercise_id))
                .first()
            )
            if duplicate:
                QMessageBox.warning(self, "Duplicado", "Ya existe otro ejercicio con ese nombre.")
                return

            exercise.nombre = nombre
            exercise.duracion_segundos = duracion
            exercise.descanso_segundos = descanso
            exercise.rondas = rondas
            exercise.descripcion = descripcion
            session.commit()

        self.load_exercises()
        idx = self.exercise_combo.findData(int(exercise_id))
        if idx >= 0:
            self.exercise_combo.setCurrentIndex(idx)

    def load_exercises(self) -> None:
        current_id = self.exercise_combo.currentData()
        self.exercise_combo.clear()

        with SessionLocal() as session:
            exercises = session.query(Ejercicio).order_by(Ejercicio.nombre.asc()).all()

        for exercise in exercises:
            label = (
                f"{exercise.nombre} "
                f"(Trabajo {exercise.duracion_segundos}s | Descanso {exercise.descanso_segundos}s | "
                f"Rondas {exercise.rondas})"
            )
            self.exercise_combo.addItem(label, exercise.id)

        if current_id is not None:
            idx = self.exercise_combo.findData(current_id)
            if idx >= 0:
                self.exercise_combo.setCurrentIndex(idx)
                return

        if self.exercise_combo.count() > 0:
            self.exercise_combo.setCurrentIndex(0)
        else:
            self.exercise_seconds = 0
            self.rest_seconds = 0
            self.total_rounds = 1
            self.current_round = 1
            self.is_rest_phase = False
            self.remaining_seconds = 0
            self._update_timer_label()
            self._update_phase_label()

    def on_exercise_selected(self) -> None:
        exercise_id = self.exercise_combo.currentData()
        if exercise_id is None:
            self.current_exercise_id = None
            self.exercise_seconds = 0
            self.rest_seconds = 0
            self.total_rounds = 1
            self.current_round = 1
            self.is_rest_phase = False
            self.remaining_seconds = 0
            self.selected_desc.clear()
            self._update_timer_label()
            self._update_phase_label()
            return

        with SessionLocal() as session:
            exercise = session.get(Ejercicio, int(exercise_id))

        if not exercise:
            return

        self.current_exercise_id = exercise.id
        self.exercise_seconds = int(exercise.duracion_segundos)
        self.rest_seconds = int(exercise.descanso_segundos)
        self.total_rounds = max(1, int(exercise.rondas))
        self.current_round = 1
        self.is_rest_phase = False
        self.remaining_seconds = self.exercise_seconds
        self.session_start = None
        self._countdown_sound_played = False
        self.timer.stop()
        self.selected_desc.setPlainText(exercise.descripcion or "Sin descripcion")
        self.exercise_name_input.setText(exercise.nombre)
        self.exercise_duration_input.setValue(self.exercise_seconds)
        self.rest_duration_input.setValue(self.rest_seconds)
        self.rounds_input.setValue(self.total_rounds)
        self.exercise_desc_input.setPlainText(exercise.descripcion or "")
        self._update_timer_label()
        self._update_phase_label()

    def delete_exercise(self) -> None:
        exercise_id = self.exercise_combo.currentData()
        if exercise_id is None:
            QMessageBox.information(self, "Sin seleccion", "Selecciona un entrenamiento para borrar.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "Se borrara el entrenamiento seleccionado y sus sesiones registradas. Continuar?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            exercise = session.get(Ejercicio, int(exercise_id))
            if not exercise:
                QMessageBox.warning(self, "No encontrado", "El entrenamiento ya no existe.")
                return
            session.delete(exercise)
            session.commit()

        self.timer.stop()
        self.session_start = None
        self.current_exercise_id = None
        self.exercise_seconds = 0
        self.rest_seconds = 0
        self.total_rounds = 1
        self.current_round = 1
        self.is_rest_phase = False
        self.remaining_seconds = 0
        self.selected_desc.clear()
        self._countdown_sound_played = False
        self._update_phase_label()
        self.load_exercises()

    def start_timer(self) -> None:
        if self.current_exercise_id is None:
            QMessageBox.information(self, "Sin ejercicio", "Primero crea o selecciona un ejercicio.")
            return

        if self.remaining_seconds <= 0:
            self.remaining_seconds = self.rest_seconds if self.is_rest_phase else self.exercise_seconds

        if self.session_start is None:
            self.session_start = datetime.now()
            self._countdown_sound_played = False
            self._start_countdown_with_horn_delay()
            return

        if not self.timer.isActive() and not self._pending_start:
            self.timer.start()

    def pause_timer(self) -> None:
        self._start_delay_timer.stop()
        self._pending_start = False
        self.timer.stop()

    def reset_timer(self) -> None:
        self._start_delay_timer.stop()
        self._pending_start = False
        self.timer.stop()
        self.current_round = 1
        self.is_rest_phase = False
        self.remaining_seconds = self.exercise_seconds
        self.session_start = None
        self._countdown_sound_played = False
        self._update_timer_label()
        self._update_phase_label()

    def _play_start_sound(self) -> None:
        if self._start_player.source().isValid():
            self._start_player.stop()
            self._start_player.play()

    def _start_countdown_with_horn_delay(self) -> None:
        self.timer.stop()
        self._play_start_sound()
        self._pending_start = True
        self._start_delay_timer.start(500)

    def _begin_countdown_after_delay(self) -> None:
        self._pending_start = False
        self.timer.start()

    def _play_countdown_sound(self) -> None:
        if self._countdown_player.source().isValid():
            self._countdown_player.stop()
            self._countdown_player.play()

    def _start_rest_phase(self) -> None:
        self.is_rest_phase = True
        self.remaining_seconds = self.rest_seconds
        self._countdown_sound_played = False
        self._update_timer_label()
        self._update_phase_label()

    def _start_next_round(self) -> None:
        self.current_round += 1
        self.is_rest_phase = False
        self.remaining_seconds = self.exercise_seconds
        self._countdown_sound_played = False
        self._update_timer_label()
        self._update_phase_label()
        self._start_countdown_with_horn_delay()

    def _finish_training(self) -> None:
        self.timer.stop()
        self._save_training_session()
        self._countdown_sound_played = False
        self.is_rest_phase = False
        self.current_round = 1
        self.remaining_seconds = self.exercise_seconds
        self._update_timer_label()
        self._update_phase_label()
        QMessageBox.information(self, "Completado", "Entrenamiento finalizado.")

    def _tick(self) -> None:
        if self.remaining_seconds <= 0:
            self.timer.stop()
            return

        self.remaining_seconds -= 1
        self._update_timer_label()

        if self.remaining_seconds == 4 and not self._countdown_sound_played:
            self._countdown_sound_played = True
            self._play_countdown_sound()

        if self.remaining_seconds == 0:
            if self.is_rest_phase:
                self._start_next_round()
                return

            if self.current_round >= self.total_rounds:
                self._finish_training()
                return

            if self.rest_seconds > 0:
                self._start_rest_phase()
            else:
                self._start_next_round()

    def _save_training_session(self) -> None:
        if self.current_exercise_id is None or self.session_start is None:
            return

        end = datetime.now()
        elapsed_seconds = max(1, int((end - self.session_start).total_seconds()))

        with SessionLocal() as session:
            sesion = SesionEntrenamiento(
                ejercicio_id=self.current_exercise_id,
                fecha_inicio=self.session_start,
                fecha_fin=end,
                duracion_real_segundos=elapsed_seconds,
            )
            session.add(sesion)
            session.commit()

        self.session_start = None

    def _update_timer_label(self) -> None:
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _update_phase_label(self) -> None:
        if self.current_exercise_id is None:
            self.phase_label.setText("Sin ejercicio")
            return

        phase = "Descanso" if self.is_rest_phase else "Ejercicio"
        self.phase_label.setText(f"{phase} - Ronda {self.current_round}/{self.total_rounds}")
