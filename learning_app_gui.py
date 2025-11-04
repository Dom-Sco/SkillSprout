import sys
import pandas as pd
import os
import shutil
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QStackedWidget, QListWidget, QFileDialog, QMessageBox, QGroupBox, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QPen, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize
from learningtree import load_learning_tree, TopicNode
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QStackedWidget, QListWidget, QLineEdit, QRadioButton, QButtonGroup
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
import json
from adaptivedifficulty import *
from qanda import load_questions_from_file, get_randomized_question
from learningtree import TopicNode, load_learning_tree 
from data import *
import copy
from nlp_utils import get_text_similarity, SIMILARITY_THRESHOLD
from progression_manager import ProgressionManager
from design_course_screen import DesignCourseScreen


COURSES_DIR = "courses"

def load_course_tree(course_name):
    file_path = os.path.join("courses", course_name, "progressiontree.json")
    return load_learning_tree(file_path)

class OutlinedLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.outline_color = QColor("black")
        self.text_color = QColor("white")
        self.outline_width = 2

    def paintEvent(self, event):
        painter = QPainter(self)
        font = self.font()
        painter.setFont(font)
        text = self.text()

        # Draw outline
        pen = QPen(self.outline_color)
        pen.setWidth(self.outline_width)
        painter.setPen(pen)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx != 0 or dy != 0:
                    painter.drawText(dx, dy + font.pointSize(), text)

        # Draw main text
        painter.setPen(self.text_color)
        painter.drawText(0, font.pointSize(), text)


class MainMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.setSpacing(40)
        layout.setAlignment(Qt.AlignCenter)

        # --- Title ---
        title_label = OutlinedLabel("SkillSprout")
        title_font = QFont("Times New Roman", 48, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)


        # --- Buttons ---
        self.select_course_btn = QPushButton("Select Course", self)
        self.design_course_btn = QPushButton("Design Course", self)

        for btn in [self.select_course_btn, self.design_course_btn]:
            btn.setFixedSize(320, 70)
            btn.setFont(QFont("Times New Roman", 18, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #66BB6A;
                    color: white;
                    border: 3px solid black;
                    border-radius: 20px;
                }
                QPushButton:hover {
                    background-color: #81C784;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

        # --- Background gradient ---
        palette = self.palette()
        gradient_color1 = QColor(85, 239, 196)   # soft mint
        gradient_color2 = QColor(29, 209, 161)   # darker teal
        palette.setColor(QPalette.Window, gradient_color1)
        self.setAutoFillBackground(True)
        self.setPalette(palette)


class CourseSelectionScreen(QWidget):
    def __init__(self, parent, app_window):
        super().__init__(parent)
        self.app_window = app_window

        # --- Layout ---
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(30)
        self.layout.setContentsMargins(40, 40, 40, 40)

        # --- Title ---
        self.title_label = OutlinedLabel("Select a Course")
        self.title_label.setFont(QFont("Times New Roman", 36, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # --- Course List ---
        self.course_list_widget = QListWidget(self)
        self.course_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #E0F2F1;
                border: 3px solid black;
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
            }
            QListWidget::item:selected {
                background-color: #81C784;
                color: white;
            }
        """)
        self.layout.addWidget(self.course_list_widget)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.add_button = QPushButton("Add Course")
        self.delete_button = QPushButton("Delete Course")
        self.select_button = QPushButton("Select Course")

        for btn in [self.add_button, self.delete_button, self.select_button]:
            btn.setFixedSize(200, 60)
            btn.setFont(QFont("Times New Roman", 16, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #66BB6A;
                    color: white;
                    border: 3px solid black;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #81C784;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
            button_layout.addWidget(btn)

        self.layout.addLayout(button_layout)

        # --- Background gradient ---
        palette = self.palette()
        gradient_color1 = QColor(204, 255, 229)  # soft mint
        gradient_color2 = QColor(178, 255, 217)  # slightly darker
        palette.setColor(QPalette.Window, gradient_color1)
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # --- Connect button signals ---
        self.add_button.clicked.connect(self.add_course)
        self.delete_button.clicked.connect(self.delete_course)
        self.select_button.clicked.connect(self.select_course)

        # --- Load courses ---
        self.refresh_course_list()


    def refresh_course_list(self):
        """Reload the list of courses from the folder."""
        self.course_list_widget.clear()
        if not os.path.exists(COURSES_DIR):
            os.makedirs(COURSES_DIR)
        courses = [name for name in os.listdir(COURSES_DIR) if os.path.isdir(os.path.join(COURSES_DIR, name))]
        self.course_list_widget.addItems(courses)

    def add_course(self):
        """Add a course by selecting an existing folder from the computer."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Course Folder")
        if not folder_path:
            return  # user cancelled

        # Check folder structure
        required_files = ["progressiontree.json", "questions.json"]
        required_dirs = ["images"]

        missing_items = []
        for f in required_files:
            if not os.path.isfile(os.path.join(folder_path, f)):
                missing_items.append(f)
        for d in required_dirs:
            if not os.path.isdir(os.path.join(folder_path, d)):
                missing_items.append(d)

        if missing_items:
            QMessageBox.warning(
                self,
                "Invalid Course",
                f"The selected folder is missing required items:\n{', '.join(missing_items)}"
            )
            return

        # Copy folder into COURSES_DIR
        course_name = os.path.basename(folder_path)
        dest_path = os.path.join(COURSES_DIR, course_name)
        if os.path.exists(dest_path):
            QMessageBox.warning(self, "Error", f"A course named '{course_name}' already exists!")
            return

        try:
            shutil.copytree(folder_path, dest_path)
            QMessageBox.information(self, "Success", f"Course '{course_name}' added successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy course: {e}")
            return

        self.refresh_course_list()

    def delete_course(self):
        """Delete the selected course folder."""
        selected = self.course_list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "No course selected!")
            return
        course_name = selected.text()
        reply = QMessageBox.question(
            self, "Delete Course", f"Are you sure you want to delete '{course_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            shutil.rmtree(os.path.join(COURSES_DIR, course_name))
            self.refresh_course_list()

    def select_course(self):
        selected = self.course_list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "No course selected!")
            return

        course_name = str(selected.text())

        # Tell the main app to show the progression tree
        self.app_window.show_progression_tree_screen(course_name)

class ProgressionTreeScreen(QWidget):
    def __init__(self, parent, course_name, app_window):
        super().__init__(parent)
        self.course_name = course_name
        self.app_window = app_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # --- Title ---
        self.title_label = OutlinedLabel(course_name)
        self.title_label.setFont(QFont("Times New Roman", 36, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # --- Background color ---
        self.setAutoFillBackground(True)
        palette = self.palette()
        self.background_color = QColor(204, 255, 229)  # mint green
        palette.setColor(QPalette.Window, self.background_color)
        self.setPalette(palette)

        # --- Matplotlib canvas ---
        self.figure, self.ax = plt.subplots(figsize=(12, 8))
        self.figure.patch.set_facecolor(self.background_color.name())
        self.ax.set_facecolor(self.background_color.name())
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # --- Load tree data ---
        self.topics = load_course_tree(course_name)

        # --- Draw tree ---
        self.draw_tree()

    def draw_tree(self):
        self.ax.clear()
        G = nx.DiGraph()
        node_colors = []
        node_names = []

        # Build graph
        for topic in self.topics:
            G.add_node(topic.name)
            node_names.append(topic.name)
            if topic.completed:
                node_colors.append("#66BB6A")  # green
            elif topic.is_available():
                node_colors.append("#FFD54F")  # yellow
            else:
                node_colors.append("#B0BEC5")  # light gray
            for prereq in topic.prerequisites:
                G.add_edge(prereq.name, topic.name)

        # --- Hierarchy layout ---
        def hierarchy_pos(G, root=None, width=1., vert_gap=1., xcenter=0.5, pos=None, parent=None):
            if pos is None:
                pos = {}
            if root is None:
                roots = [n for n, d in G.in_degree() if d == 0]
                if not roots:
                    raise ValueError("No root found")
                root = roots[0]

            y = 0 if parent is None else pos[parent][1] - vert_gap
            pos[root] = (xcenter, y)

            children = list(G.successors(root))
            if children:
                dx = width / len(children)
                left = xcenter - width / 2
                for i, child in enumerate(children):
                    child_x = left + dx/2 + i*dx
                    pos = hierarchy_pos(G, root=child, width=dx, vert_gap=vert_gap,
                                        xcenter=child_x, pos=pos, parent=root)
            return pos

        pos = hierarchy_pos(G, vert_gap=1.5)

        # --- Draw nodes ---
        nodes_collection = nx.draw_networkx_nodes(
            G, pos,
            node_color=node_colors,
            edgecolors="black",
            linewidths=2,
            node_size=5000,
            ax=self.ax
        )
        nodes_collection.set_picker(True)
        nodes_collection.set_pickradius(15)
        self.nodes_collection = nodes_collection
        self.node_names = node_names  # for mapping clicks

        # --- Draw edges ---
        nx.draw_networkx_edges(
            G, pos,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=20,
            ax=self.ax
        )

        # --- Draw labels ---
        nx.draw_networkx_labels(
            G, pos,
            labels={t.name: t.name for t in self.topics},
            font_size=12,
            font_weight="bold",
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),
            ax=self.ax
        )

        self.ax.set_axis_off()
        self.canvas.draw()

        # --- Connect click event ---
        self.canvas.mpl_connect("pick_event", self.on_node_click)

    def on_node_click(self, event):
        if event.artist != self.nodes_collection:
            return
        ind = event.ind[0]
        node_name = self.node_names[ind]
        self.show_node_popup(node_name)

    def show_node_popup(self, node_name):
        # Look up the TopicNode object by name
        topic = next((t for t in self.topics if t.name == node_name), None)
        if topic is None:
            return

        # --- Safely close any existing popup ---
        if hasattr(self, 'popup') and self.popup is not None:
            try:
                if self.popup.isVisible():
                    self.popup.close()
            except RuntimeError:
                # Already deleted
                pass

        # --- Create new popup ---
        self.popup = QWidget(self)
        self.popup.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.popup.setAttribute(Qt.WA_DeleteOnClose)
        self.popup.setFixedSize(400, 300)

        # Center the popup
        parent_rect = self.rect()
        self.popup.move(
            parent_rect.center().x() - self.popup.width() // 2,
            parent_rect.center().y() - self.popup.height() // 2
        )

        # --- Styling ---
        self.popup.setStyleSheet("""
            background-color: #E1F5FE;
            border: 3px solid black;
            border-radius: 15px;
        """)

        layout = QVBoxLayout(self.popup)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # --- Close button ---
        close_btn = QPushButton("X", self.popup)
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            background-color: red;
            color: white;
            border: none;
            font-weight: bold;
            border-radius: 15px;
        """)
        close_btn.clicked.connect(self.popup.close)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        # --- Topic label ---
        topic_label = QLabel(f"Topic: {topic.name}", self.popup)
        topic_label.setFont(QFont("Times New Roman", 16, QFont.Bold))
        topic_label.setAlignment(Qt.AlignCenter)
        topic_label.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(topic_label)

        # --- Load stats from CSV ---
        stats_text = "No data available for this topic."
        user_data_file = os.path.join(COURSES_DIR, self.course_name, "user_data.csv")
        if os.path.exists(user_data_file):
            import pandas as pd
            df = pd.read_csv(user_data_file)
            if 'topic' in df.columns:
                # Map TopicNode to its numeric index in the CSV
                topic_index = self.topics.index(topic)
                topic_df = df[df['topic'] == topic_index]

                if not topic_df.empty:
                    total_questions = len(topic_df)
                    avg_time = topic_df['time_on_question'].mean()
                    correct_count = topic_df['correct'].sum()
                    accuracy = (correct_count / total_questions) * 100
                    max_streak = topic_df['correct_streak'].max()
                    stats_text = (
                        f"Questions attempted: {total_questions}\n"
                        f"Average time: {avg_time:.1f}s\n"
                        f"Accuracy: {accuracy:.1f}%\n"
                        f"Max correct streak: {max_streak}"
                    )

        stats_label = QLabel(stats_text, self.popup)
        stats_label.setAlignment(Qt.AlignCenter)
        stats_label.setFont(QFont("Times New Roman", 14))
        layout.addWidget(stats_label)

        # --- Practice questions button ---
        practice_btn = QPushButton("Practice Questions", self.popup)
        practice_btn.setFixedSize(180, 40)
        practice_btn.setFont(QFont("Times New Roman", 12, QFont.Bold))
        practice_btn.setStyleSheet("""
            background-color: #66BB6A;
            color: white;
            border: 2px solid black;
            border-radius: 10px;
        """)
        layout.addWidget(practice_btn, alignment=Qt.AlignCenter)

        # --- Connect button to open QuestionScreen ---
        def open_questions_from_popup():
            if self.popup is not None:
                try:
                    self.popup.close()
                except RuntimeError:
                    pass

            self.app_window.show_question_screen(node_name)

        practice_btn.clicked.connect(open_questions_from_popup)

        self.popup.show()


    def open_questions_from_popup():
        if self.popup is not None:
            try:
                self.popup.close()
            except RuntimeError:
                pass
        # Call the main app's method
        self.app_window.show_question_screen(topic.name)


class QuestionScreen(QWidget):
    def __init__(self, parent, selected_topic, app_window):
        super().__init__(parent)
        self.selected_topic = selected_topic
        self.app_window = app_window
        self.course_name = getattr(app_window, "current_course", None)

        if not self.course_name:
            print("⚠️ No course context found. Cannot load questions.")
            return

        # --- Screen layout ---
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        self.setLayout(self.layout)

        # --- Main gradient background ---
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #A1C4FD, stop:1 #C2E9FB
                );
            }
        """)

        # --- Card frame ---
        self.card_frame = QFrame(self)
        self.card_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F8FF;  /* GhostWhite, subtle off-white */
                border: 2px solid black;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card_frame.setGraphicsEffect(shadow)

        self.card_layout = QVBoxLayout(self.card_frame)
        self.card_layout.setSpacing(15)
        self.layout.addWidget(self.card_frame, alignment=Qt.AlignCenter)

        # --- Topic Label ---
        self.title_label = QLabel(self.selected_topic)
        self.title_label.setFont(QFont("Times New Roman", 20, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.title_label)

        # --- Image ---
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setVisible(False)
        self.card_layout.addWidget(self.image_label)

        # --- Question Text ---
        self.question_text = QLabel("")
        self.question_text.setWordWrap(True)
        self.question_text.setAlignment(Qt.AlignCenter)
        self.question_text.setFont(QFont("Times New Roman", 16))
        self.card_layout.addWidget(self.question_text)

        # --- Feedback Label ---
        self.question_label = QLabel("")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setFont(QFont("Times New Roman", 14, QFont.Bold))
        self.card_layout.addWidget(self.question_label)

        # --- Multiple choice container ---
        self.choices_container = QFrame()
        self.choices_layout = QVBoxLayout(self.choices_container)
        self.choices_layout.setSpacing(10)
        self.choices_container.setVisible(False)
        self.card_layout.addWidget(self.choices_container)
        self.choices_group = None

        # --- Input field ---
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Enter your answer here")
        self.card_layout.addWidget(self.answer_input)

        # --- Buttons ---
        self.submit_button = QPushButton("Submit")
        self.next_button = QPushButton("Next Question")
        self.next_button.setEnabled(False)
        self.back_button = QPushButton("Back to Topics")

        for btn in [self.submit_button, self.next_button, self.back_button]:
            btn.setFixedHeight(45)
            btn.setFont(QFont("Times New Roman", 12, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #66BB6A;
                    color: white;
                    border: 2px solid black;
                    border-radius: 12px;
                }
                QPushButton:hover { background-color: #81C784; }
                QPushButton:pressed { background-color: #388E3C; }
            """)

        # --- Button layout ---
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.submit_button)
        btn_layout.addWidget(self.next_button)
        btn_layout.addWidget(self.back_button)
        self.card_layout.addLayout(btn_layout)

        # --- Timer and Q-learning placeholders ---
        self.timer = QTimer(self)
        self.time_spent = 0
        self.q_learning_agent = getattr(app_window, "q_learning_agent", None)

        # --- Connect buttons ---
        self.submit_button.clicked.connect(self.on_submit_answer)
        self.next_button.clicked.connect(self.on_next_question)
        self.back_button.clicked.connect(self.on_back_to_topics)

        # --- Load first question ---
        self.load_random_question()

    # ------------------- IMAGE -------------------
    def display_image(self, image_path):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(
                pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.image_label.setStyleSheet("""
                border: 2px solid black;
                border-radius: 10px;
                margin: 0px;
                padding: 0px;
            """)
            self.image_label.setVisible(True)
        else:
            self.image_label.setVisible(False)

    def check_topic_mastery_and_notify(self):
        """
        Check if the current topic is mastered and display a brief popup if so.
        """

        # Load topic progression JSON
        progression_file = os.path.join("courses", self.course_name, "progressiontree.json")
        manager = ProgressionManager(progression_file)

        # Compute stats for this topic from CSV
        import pandas as pd
        user_data_file = os.path.join("courses", self.course_name, "user_data.csv")
        stats = {"n_attempts": 0, "n_correct": 0, "avg_similarity": 0.0, "streak": 0}
        if os.path.exists(user_data_file):
            df = pd.read_csv(user_data_file)
            topic_index = [t["name"] for t in manager.topics.values()].index(self.selected_topic)
            topic_df = df[df["topic"] == topic_index]
            if not topic_df.empty:
                stats["n_attempts"] = len(topic_df)
                stats["n_correct"] = topic_df["correct"].sum()
                stats["streak"] = topic_df["correct_streak"].max()
                if 'submitted_answer' in topic_df.columns and 'correct_answer' in topic_df.columns:
                    stats["avg_similarity"] = topic_df["submitted_answer"].mean()  # approximate

        # Check mastery
        mastered = manager.is_topic_mastered(self.selected_topic, stats)
        if mastered and not getattr(self, "_topic_mastered_flag", False):
            self._topic_mastered_flag = True  # prevent repeated popups

            # --- Create brief popup ---
            popup = QFrame(self)
            popup.setStyleSheet("""
                QFrame {
                    background-color: #66BB6A;
                    color: white;
                    border: 2px solid black;
                    border-radius: 10px;
                }
            """)
            popup.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
            popup.setFixedSize(250, 80)

            label = QLabel("🎉 Topic Mastered!", popup)
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Times New Roman", 16, QFont.Bold))

            layout = QVBoxLayout(popup)
            layout.addWidget(label)
            popup.setLayout(layout)

            # Center popup over QuestionScreen
            parent_rect = self.rect()
            popup.move(
                parent_rect.center().x() - popup.width() // 2,
                parent_rect.center().y() - popup.height() // 2
            )

            popup.show()

            # Auto-close after 2 seconds
            QTimer.singleShot(2000, popup.close)

    # ------------------- LOAD QUESTION -------------------
    def load_random_question(self):
        """Load a random question for this topic."""
        self.time_spent = 0
        self.question_label.setText("")  # clear feedback

        # --- Build path ---
        questions_path = os.path.join("courses", self.course_name, "questions.json")
        if not os.path.exists(questions_path):
            self.question_text.setText(f"❌ Error: questions.json not found at {questions_path}")
            self.image_label.setVisible(False)
            return

        # --- Q-learning chooses difficulty ---
        try:
            difficulty = self.q_learning_agent.choose_action()
            question_text, numeric_answer, question_instance = get_randomized_question(
                self.selected_topic,
                difficulty=difficulty,
                questions_path=questions_path
            )
        except Exception as e:
            self.question_text.setText(f"⚠️ Error loading question: {e}")
            self.image_label.setVisible(False)
            return

        if question_instance is None:
            self.question_text.setText("No questions available for this topic.")
            self.image_label.setVisible(False)
            return

        self.question_instance = copy.deepcopy(question_instance)
        self.correct_answer = getattr(self.question_instance, "correct_answer", None)
        self.difficulty = getattr(self.question_instance, "difficulty", "medium")

        # --- Display image ---
        img_filename = getattr(self.question_instance, "image", None)
        if img_filename:
            img_path = os.path.join("courses", self.course_name, "images", img_filename)
            self.display_image(img_path)
        else:
            self.image_label.setVisible(False)

        # --- Display question text ---
        self.question_text.setText(question_text)

        # --- Reset input / multiple choice ---
        self.answer_input.clear()
        self.answer_input.show()
        self.submit_button.setEnabled(True)
        self.next_button.setEnabled(False)

        for i in reversed(range(self.choices_layout.count())):
            widget = self.choices_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.choices_group = None
        self.choices_container.setVisible(False)

        if getattr(self.question_instance, "choices", None):
            self.answer_input.hide()
            self.choices_container.setVisible(True)
            self.choices_group = QButtonGroup(self)
            for choice in self.question_instance.choices:
                btn = QRadioButton(choice)
                btn.setFont(QFont("Times New Roman", 14))
                btn.setStyleSheet("""
                    QRadioButton::indicator { width: 20px; height: 20px; border-radius: 10px; border: 2px solid black; background: white; }
                    QRadioButton::indicator:checked { background-color: #66BB6A; border: 2px solid black; }
                    QRadioButton { spacing: 10px; }
                """)
                self.choices_layout.addWidget(btn)
                self.choices_group.addButton(btn)
            self.choices_group.buttonClicked.connect(lambda: self.submit_button.setEnabled(True))

        # --- Start timer ---
        self.timer.start(1000)

        # --- NEW: Check progression for this topic ---
        try:
            import pandas as pd
            csv_path = os.path.join("courses", self.course_name, "user_data.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                topic_index = next((i for i, t in enumerate(self.app_window.progression_manager.topics)
                                    if t == self.selected_topic), 0)
                topic_df = df[df["topic"] == topic_index]

                stats = {
                    "n_attempts": len(topic_df),
                    "n_correct": topic_df["correct"].sum(),
                    "avg_similarity": topic_df["submitted_answer"].mean() if not topic_df.empty else 0.0,
                    "streak": topic_df["correct_streak"].max() if not topic_df.empty else 0
                }

                newly_mastered, newly_unlocked = self.app_window.progression_manager.check_and_update_progress(
                    {self.selected_topic: stats}
                )

                # Refresh tree so unlocked topics appear
                self.app_window.progression_screen.draw_tree()

        except Exception as e:
            print(f"⚠️ Progression check failed: {e}")



    def increment_time(self):
        self.time_spent += 1

    def on_submit_answer(self):
        """Handle answer submission."""
        self.timer.stop()

        qtype = getattr(self.question_instance, "question_type", 0)
        exact_match = getattr(self.question_instance, "exact_match", False)
        correct = False
        user_answer = None

        # --- Determine correctness ---
        if qtype == 1:  # multiple choice
            selected_btn = self.choices_group.checkedButton()
            if selected_btn:
                user_answer = selected_btn.text()
                correct = user_answer == self.question_instance.evaluated_answer

        else:  # numeric or text
            user_answer = self.answer_input.text().strip()
            correct_val = getattr(self.question_instance, "evaluated_answer", None)

            if qtype == 2:  # text-based question
                try:
                    from nlp_utils import check_text_answer, get_text_similarity
                    if exact_match:
                        correct = str(user_answer).strip().lower() == str(correct_val).strip().lower()
                        similarity = 1.0 if correct else get_text_similarity(user_answer, correct_val)
                    else:
                        similarity = get_text_similarity(user_answer, correct_val)
                        correct = similarity >= 0.8  # adjustable global threshold
                except Exception as e:
                    print(f"⚠️ Text similarity check failed: {e}")
                    similarity = 0.0
                    correct = False

            else:  # numeric input
                try:
                    user_val = float(user_answer)
                    correct = float(user_val) == float(correct_val)
                except Exception:
                    correct = str(user_answer).strip().lower() == str(correct_val).strip().lower()

        # --- Feedback ---
        if qtype == 2:
            feedback = "✅ Correct!" if correct else f"❌ Incorrect. Correct answer: {correct_val}"
            if not exact_match:
                feedback += f" (Similarity: {similarity:.2f})"
        else:
            feedback = "✅ Correct!" if correct else f"❌ Incorrect. Correct answer: {self.question_instance.evaluated_answer}"

        self.question_label.setText(feedback)

        # --- Update Q-learning ---
        reward = 1.0 if correct else 0.0
        next_state = self.q_learning_agent.state.copy()
        next_state["total_questions"] += 1
        next_state["total_correct"] += int(correct)

        self.q_learning_agent.update_q_table(self.difficulty, reward, next_state)
        self.q_learning_agent.state = next_state

        # --- Store CSV data ---
        self.store_user_data(user_answer, correct)
        self.check_topic_mastery_and_notify()

        # --- Update topic progression ---
        import pandas as pd
        csv_path = os.path.join("courses", self.course_name, "user_data.csv")
        df = pd.read_csv(csv_path)

        topic_index = next((i for i, t in enumerate(self.app_window.progression_manager.topics)
                            if t == self.selected_topic), 0)
        topic_df = df[df["topic"] == topic_index]

        stats = {
            "n_attempts": len(topic_df),
            "n_correct": topic_df["correct"].sum(),
            "avg_similarity": topic_df["submitted_answer"].mean(),
            "streak": topic_df["correct_streak"].max() if not topic_df.empty else 0
        }

        newly_mastered, newly_unlocked = self.app_window.progression_manager.check_and_update_progress(
            {self.selected_topic: stats}
        )

        # --- Refresh tree GUI ---
        self.app_window.progression_screen.draw_tree()

        # --- Enable next question ---
        self.submit_button.setEnabled(False)
        self.next_button.setEnabled(True)


    def on_next_question(self):
        """Load another random question."""
        self.load_random_question()

    def on_back_to_topics(self):
        """Return to the progression tree screen."""
        self.app_window.stack.setCurrentWidget(self.app_window.progression_screen)

    def store_user_data(self, user_answer, correct):
        """Save numeric or text results to user_data.csv inside the course folder."""

        file_path = os.path.join("courses", self.course_name, "user_data.csv")
        file_exists = os.path.isfile(file_path)

        # --- Get topic index ---
        topic_id = 0
        try:
            topics = load_course_tree(self.course_name)
            topic_obj = next((t for t in topics if t.name == self.selected_topic), None)
            topic_id = topics.index(topic_obj) if topic_obj else 0
        except Exception as e:
            print(f"⚠️ Could not determine topic index: {e}")

        qtype = getattr(self.question_instance, "question_type", 0)
        exact_match = getattr(self.question_instance, "exact_match", False)
        correct_flag = int(correct)

        submitted_numeric = 0.0
        correct_numeric = 0.0

        if qtype == 2:  # text question
            from nlp_utils import get_text_similarity
            try:
                if exact_match:
                    submitted_numeric = 1.0 if str(user_answer).strip().lower() == str(self.correct_answer).strip().lower() else 0.0
                else:
                    submitted_numeric = get_text_similarity(user_answer, self.correct_answer)
                correct_numeric = 1.0 if correct else 0.0
            except Exception as e:
                print(f"⚠️ Could not compute text similarity: {e}")
                submitted_numeric = 0.0
                correct_numeric = 0.0
        else:
            # numeric or multiple-choice
            try:
                submitted_numeric = float(user_answer)
            except Exception:
                submitted_numeric = 0.0
            try:
                correct_numeric = float(self.correct_answer)
            except Exception:
                correct_numeric = 0.0

        # --- Handle streak ---
        prev_streak = 0
        if os.path.exists(file_path):
            import pandas as pd
            df = pd.read_csv(file_path)
            if not df.empty and "correct_streak" in df.columns:
                prev_streak = int(df["correct_streak"].iloc[-1]) if df["correct"].iloc[-1] == 1 else 0
        new_streak = prev_streak + 1 if correct_flag else 0

        # --- Write data row ---
        fieldnames = [
            "time_on_question",
            "difficulty",
            "topic",
            "question_type",
            "submitted_answer",
            "correct_answer",
            "correct",
            "correct_streak"
        ]

        row = {
            "time_on_question": float(self.time_spent),
            "difficulty": int(self.difficulty) if str(self.difficulty).isdigit() else 1,
            "topic": int(topic_id),
            "question_type": int(qtype),
            "submitted_answer": submitted_numeric,
            "correct_answer": correct_numeric,
            "correct": correct_flag,
            "correct_streak": new_streak
        }

        with open(file_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"✅ Saved data row: {row}")



# Main Application Window
class SkillSproutApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkillSprout")
        self.setWindowIcon(QIcon("sprout.png"))
        self.setGeometry(100, 100, 900, 650)

        # --- Initialize Q-learning agent ---
        self.q_learning_agent = AdaptiveDifficultyQlearning(csv_file=os.path.join(COURSES_DIR, "user_data.csv"))

        # --- Stacked widget to manage multiple screens ---
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # --- Screens ---
        self.main_menu = MainMenu(self)
        self.course_selection_screen = CourseSelectionScreen(self, self)
        self.design_course_screen = DesignCourseScreen(self)

        # Add screens to the stack
        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.course_selection_screen)
        self.stack.addWidget(self.design_course_screen)

        # Connect buttons to navigate
        self.main_menu.select_course_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.course_selection_screen)
        )
        self.main_menu.design_course_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.design_course_screen)
        )

        self.design_course_screen.return_to_main_menu.connect(self.show_main_menu)

        self.showMaximized()

    def show_progression_tree_screen(self, course_name):
        self.current_course = course_name

        # Initialize progression manager
        json_path = os.path.join("courses", course_name, "progressiontree.json")
        self.progression_manager = ProgressionManager(json_path)

        if hasattr(self, 'progression_screen'):
            self.stack.removeWidget(self.progression_screen)
            self.progression_screen.deleteLater()

        self.progression_screen = ProgressionTreeScreen(self, course_name, self)
        self.stack.addWidget(self.progression_screen)
        self.stack.setCurrentWidget(self.progression_screen)



    def show_question_screen(self, selected_topic):
        # Remove previous question_screen if exists
        if hasattr(self, 'question_screen'):
            self.stack.removeWidget(self.question_screen)
            self.question_screen.deleteLater()

        self.question_screen = QuestionScreen(self, selected_topic, self)
        self.stack.addWidget(self.question_screen)
        self.stack.setCurrentWidget(self.question_screen)

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)


def main():
    app = QApplication(sys.argv)
    window = SkillSproutApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
