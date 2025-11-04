import os
import json
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QTextEdit,
    QFileDialog, QLabel, QLineEdit, QMessageBox, QFormLayout, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal


class DesignCourseScreen(QWidget):
    """
    Screen for creating or editing a course consisting of:
    - progressiontree.json (topics)
    - questions.json (questions grouped by topic)
    - user_data.csv (tracks user interactions)
    """
    return_to_main_menu = pyqtSignal()  # 🔹 Signal to switch back to MainMenu

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Course Designer")

        self.course_path = None
        self.questions_data = {}
        self.progression_data = {}

        # ------------------ INITIAL LAYOUT ------------------
        self.layout = QVBoxLayout(self)
        self.init_start_screen()

    # ======================================================
    # 1️⃣ STARTUP SCREEN
    # ======================================================
    def init_start_screen(self):
        """Initial view: load or create a course."""
        self.clear_layout(self.layout)

        title = QLabel("<h2>Course Designer</h2>")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        btn_load = QPushButton("Load Existing Course")
        btn_create = QPushButton("Create New Course")

        btn_load.clicked.connect(self.load_course)
        btn_create.clicked.connect(self.create_new_course)

        hl = QHBoxLayout()
        hl.addStretch()
        hl.addWidget(btn_load)
        hl.addWidget(btn_create)
        hl.addStretch()

        self.layout.addLayout(hl)

    # ======================================================
    # 2️⃣ MAIN COURSE EDITOR
    # ======================================================
    def init_course_editor(self):
        """Main editor layout after loading or creating a course."""
        self.clear_layout(self.layout)

        # --- Top bar ---
        top_layout = QHBoxLayout()
        self.course_label = QLabel(f"Editing: {os.path.basename(self.course_path)}")
        self.save_btn = QPushButton("💾 Save")
        self.back_btn = QPushButton("⬅ Return to Main Menu")

        self.save_btn.clicked.connect(self.save_course)
        self.back_btn.clicked.connect(self.return_to_main_menu.emit)  # 🔹 Emits signal

        top_layout.addWidget(self.course_label)
        top_layout.addStretch()
        top_layout.addWidget(self.back_btn)
        top_layout.addWidget(self.save_btn)
        self.layout.addLayout(top_layout)

        # --- Split view ---
        main_layout = QHBoxLayout()
        self.layout.addLayout(main_layout)

        # Left: topic list
        topic_panel = QVBoxLayout()
        self.topic_list = QListWidget()
        self.topic_list.itemSelectionChanged.connect(self.on_topic_selected)
        topic_panel.addWidget(QLabel("<b>Topics</b>"))
        topic_panel.addWidget(self.topic_list)

        add_topic_btn = QPushButton("➕ Add Topic")
        del_topic_btn = QPushButton("❌ Remove Topic")
        add_topic_btn.clicked.connect(self.add_topic)
        del_topic_btn.clicked.connect(self.remove_topic)

        hl = QHBoxLayout()
        hl.addWidget(add_topic_btn)
        hl.addWidget(del_topic_btn)
        topic_panel.addLayout(hl)
        main_layout.addLayout(topic_panel, 2)

        # Right: question editor
        self.question_panel = QVBoxLayout()
        self.question_panel.addWidget(QLabel("<b>Questions</b>"))

        self.question_list = QListWidget()
        self.question_list.itemSelectionChanged.connect(self.on_question_selected)
        self.question_panel.addWidget(self.question_list)

        q_btns = QHBoxLayout()
        self.add_q_btn = QPushButton("Add Question")
        self.del_q_btn = QPushButton("Remove Question")
        q_btns.addWidget(self.add_q_btn)
        q_btns.addWidget(self.del_q_btn)
        self.add_q_btn.clicked.connect(self.add_question)
        self.del_q_btn.clicked.connect(self.remove_question)
        self.question_panel.addLayout(q_btns)

        # Question form editor
        self.question_form = self.create_question_form()
        self.question_panel.addWidget(self.question_form)

        main_layout.addLayout(self.question_panel, 5)

        self.refresh_topics()

    # ======================================================
    # 3️⃣ COURSE CREATION / LOADING
    # ======================================================
    def create_new_course(self):
        """Create a new empty course folder and user_data.csv."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Create Course In")
        if not folder:
            return

        name, ok = QFileDialog.getSaveFileName(self, "Enter course name (without extension)", folder, "Text Files (*.txt)")
        if not ok:
            return

        course_name = os.path.splitext(os.path.basename(name))[0]
        course_folder = os.path.join(folder, course_name)
        os.makedirs(course_folder, exist_ok=True)
        os.makedirs(os.path.join(course_folder, "images"), exist_ok=True)

        # Create empty structure
        self.progression_data = {"topics": []}
        self.questions_data = {}

        with open(os.path.join(course_folder, "progressiontree.json"), "w") as f:
            json.dump(self.progression_data, f, indent=2)
        with open(os.path.join(course_folder, "questions.json"), "w") as f:
            json.dump(self.questions_data, f, indent=2)

        # Create user_data.csv with headers
        user_data_file = os.path.join(course_folder, "user_data.csv")
        with open(user_data_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "time_on_question", "difficulty", "topic", "question_type",
                "submitted_answer", "correct_answer", "correct", "correct_streak"
            ])

        self.course_path = course_folder
        self.init_course_editor()

    def load_course(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Course Folder")
        if not folder:
            return

        qfile = os.path.join(folder, "questions.json")
        pfile = os.path.join(folder, "progressiontree.json")

        if not os.path.exists(qfile) or not os.path.exists(pfile):
            QMessageBox.warning(self, "Missing Files", "This folder must contain questions.json and progressiontree.json")
            return

        with open(qfile, "r") as f:
            self.questions_data = json.load(f)

        with open(pfile, "r") as f:
            self.progression_data = json.load(f)

        self.course_path = folder
        self.init_course_editor()

    # ======================================================
    # 4️⃣ TOPIC MANAGEMENT
    # ======================================================
    def refresh_topics(self):
        self.topic_list.clear()
        for topic in self.progression_data.get("topics", []):
            self.topic_list.addItem(topic["name"])

    def add_topic(self):
        name, ok = QInputDialog.getText(self, "New Topic", "Enter topic name:")
        if not ok or not name.strip():
            return
        new_topic = {
            "name": name.strip(),
            "prerequisites": [],
            "completed": False,
            "conditions": {"min_questions": 5, "min_accuracy": 0.8, "min_streak": 3}
        }
        self.progression_data.setdefault("topics", []).append(new_topic)
        self.questions_data[new_topic["name"]] = []
        self.refresh_topics()

    def remove_topic(self):
        items = self.topic_list.selectedItems()
        if not items:
            return
        name = items[0].text()
        self.progression_data["topics"] = [t for t in self.progression_data["topics"] if t["name"] != name]
        if name in self.questions_data:
            del self.questions_data[name]
        self.refresh_topics()
        self.question_list.clear()

    def on_topic_selected(self):
        items = self.topic_list.selectedItems()
        if not items:
            return
        name = items[0].text()
        questions = self.questions_data.get(name, [])
        self.refresh_questions(questions)

    # ======================================================
    # 5️⃣ QUESTION MANAGEMENT
    # ======================================================
    def refresh_questions(self, questions):
        self.question_list.clear()
        for q in questions:
            self.question_list.addItem(q["question"])

    def add_question(self):
        topic = self.get_current_topic()
        if not topic:
            return
        new_q = {
            "question": "New question text",
            "difficulty": 1,
            "randomize": False,
            "is_integer": False,
            "params": {},
            "correct_answer": "",
            "image": None,
            "choices": [],
            "question_type": 0,
            "exact_match": False
        }
        self.questions_data.setdefault(topic, []).append(new_q)
        self.refresh_questions(self.questions_data[topic])

    def remove_question(self):
        topic = self.get_current_topic()
        items = self.question_list.selectedItems()
        if not topic or not items:
            return
        question_text = items[0].text()
        self.questions_data[topic] = [q for q in self.questions_data[topic] if q["question"] != question_text]
        self.refresh_questions(self.questions_data[topic])

    def on_question_selected(self):
        topic = self.get_current_topic()
        items = self.question_list.selectedItems()
        if not topic or not items:
            return
        question_text = items[0].text()
        q = next((q for q in self.questions_data[topic] if q["question"] == question_text), None)
        if not q:
            return
        self.load_question_into_form(q)

    def get_current_topic(self):
        items = self.topic_list.selectedItems()
        return items[0].text() if items else None

    # ======================================================
    # 6️⃣ QUESTION FORM
    # ======================================================
    def create_question_form(self):
        group = QGroupBox("Edit Question")
        form = QFormLayout()

        self.q_text = QTextEdit()
        self.q_difficulty = QSpinBox()
        self.q_difficulty.setRange(1, 10)
        self.q_randomize = QCheckBox()
        self.q_is_integer = QCheckBox()
        self.q_params = QTextEdit()
        self.q_correct = QLineEdit()
        self.q_image = QLineEdit()
        self.q_type = QComboBox()
        self.q_type.addItems(["0 - Numeric", "1 - Multiple Choice", "2 - Text"])
        self.q_exact = QCheckBox()

        form.addRow("Question Text:", self.q_text)
        form.addRow("Difficulty (1-10):", self.q_difficulty)
        form.addRow("Randomize:", self.q_randomize)
        form.addRow("Is Integer:", self.q_is_integer)
        form.addRow("Params (JSON):", self.q_params)
        form.addRow("Correct Answer:", self.q_correct)
        form.addRow("Image Path:", self.q_image)
        form.addRow("Question Type:", self.q_type)
        form.addRow("Exact Match:", self.q_exact)

        save_btn = QPushButton("Update Question")
        save_btn.clicked.connect(self.update_question)
        form.addRow(save_btn)

        group.setLayout(form)
        return group

    def load_question_into_form(self, q):
        self.q_text.setPlainText(q["question"])
        self.q_difficulty.setValue(q["difficulty"])
        self.q_randomize.setChecked(q["randomize"])
        self.q_is_integer.setChecked(q["is_integer"])
        self.q_params.setPlainText(json.dumps(q["params"], indent=2))
        self.q_correct.setText(q["correct_answer"])
        self.q_image.setText(q["image"] or "")
        self.q_type.setCurrentIndex(q["question_type"])
        self.q_exact.setChecked(q["exact_match"])

    def update_question(self):
        topic = self.get_current_topic()
        items = self.question_list.selectedItems()
        if not topic or not items:
            return
        question_text = items[0].text()
        q = next((q for q in self.questions_data[topic] if q["question"] == question_text), None)
        if not q:
            return

        try:
            q["params"] = json.loads(self.q_params.toPlainText())
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Invalid JSON", "Params field must contain valid JSON.")
            return

        q.update({
            "question": self.q_text.toPlainText(),
            "difficulty": self.q_difficulty.value(),
            "randomize": self.q_randomize.isChecked(),
            "is_integer": self.q_is_integer.isChecked(),
            "correct_answer": self.q_correct.text(),
            "image": self.q_image.text() or None,
            "question_type": self.q_type.currentIndex(),
            "exact_match": self.q_exact.isChecked()
        })

        self.refresh_questions(self.questions_data[topic])

    # ======================================================
    # 7️⃣ SAVE COURSE
    # ======================================================
    def save_course(self):
        if not self.course_path:
            return
        with open(os.path.join(self.course_path, "progressiontree.json"), "w") as f:
            json.dump(self.progression_data, f, indent=2)
        with open(os.path.join(self.course_path, "questions.json"), "w") as f:
            json.dump(self.questions_data, f, indent=2)
        QMessageBox.information(self, "Saved", "Course saved successfully.")

    # ======================================================
    # Utility
    # ======================================================
    @staticmethod
    def clear_layout(layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
