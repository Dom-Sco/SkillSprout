import random
import json
import copy
import os

class Question:
    def __init__(self,
                 question_text,
                 difficulty,
                 params=None,
                 randomize=False,
                 correct_answer=None,
                 image=None,
                 is_integer=False,
                 question_type=0,
                 choices=None,
                 exact_match=False):
        self.question_text = question_text
        self.difficulty = difficulty
        self.params = params or {}
        self.randomize = randomize
        self.correct_answer = correct_answer
        self.image = image
        self.is_integer = is_integer
        self.question_type = question_type  # 0 numeric, 1 multiple-choice, 2 text
        self.choices = choices or []
        self.exact_match = exact_match
        self.evaluated_answer = None
        self.randomized_params = {}

    def generate_param_value(self, param_config):
        """Generate a parameter value (gaussian) and round if integer."""
        base_value = param_config.get("value", 0)
        sd = param_config.get("sd", 0)
        value = random.gauss(base_value, sd)
        return int(round(value)) if self.is_integer else round(value, 2)

    def generate_question(self):
        """Generate question text and evaluate numeric correct answer."""
        randomized_params = {}
        for param, values in self.params.items():
            if self.randomize:
                randomized_params[param] = self.generate_param_value(values)
            else:
                randomized_params[param] = values.get("value", values) if isinstance(values, dict) else values

        # Format question text
        try:
            question_text = self.question_text.format(**randomized_params)
        except Exception as e:
            print(f"⚠️ Error formatting question text: {e}")
            question_text = self.question_text

        # Evaluate correct answer
        correct_answer_val = self.correct_answer
        if isinstance(self.correct_answer, str) and "{" in self.correct_answer:
            try:
                expr = self.correct_answer.format(**randomized_params)
                correct_answer_val = eval(expr, {"__builtins__": {}})
            except Exception as e:
                print(f"⚠️ Error evaluating correct_answer '{self.correct_answer}' with {randomized_params}: {e}")
                correct_answer_val = 0

        # Ensure numeric type
        try:
            correct_answer_val = float(correct_answer_val)
        except Exception:
            correct_answer_val = correct_answer_val

        if self.is_integer and correct_answer_val is not None:
            try:
                correct_answer_val = int(round(correct_answer_val))
            except Exception:
                pass

        self.randomized_params = randomized_params
        self.evaluated_answer = correct_answer_val

        return question_text, correct_answer_val, randomized_params

    def calculate_answer(self, params=None):
        """Evaluate correct answer for given parameters."""
        if params is None:
            params = getattr(self, "randomized_params", {}) or {}

        ans = self.correct_answer
        if isinstance(self.correct_answer, str) and "{" in self.correct_answer:
            try:
                expr = self.correct_answer.format(**params)
                ans = eval(expr, {"__builtins__": {}})
            except Exception as e:
                print(f"qanda.calculate_answer: failed to evaluate '{self.correct_answer}' with {params}: {e}")
                ans = 0

        try:
            ans = float(ans)
        except Exception:
            pass

        if self.is_integer and ans is not None:
            try:
                ans = int(round(ans))
            except Exception:
                pass

        return ans

    def check_answer(self, user_answer):
        """Compare user answer to evaluated answer."""
        correct_val = getattr(self, "evaluated_answer", self.correct_answer)
        try:
            user_val = float(user_answer)
            correct = abs(user_val - float(correct_val)) < 1e-6
        except Exception:
            correct = str(user_answer).strip().lower() == str(correct_val).strip().lower()
        return correct


def load_questions_from_file(questions_path=None):
    """Load questions.json and return {topic: [Question, ...]}"""
    if questions_path is None:
        questions_path = os.path.join("trees", "questions.json")

    if not os.path.exists(questions_path):
        print(f"❌ questions.json not found at {questions_path}")
        return {}

    with open(questions_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    questions_data = {}
    for topic, qlist in raw.items():
        out_list = []
        for q in qlist:
            qobj = Question(
                question_text=q.get("question", ""),
                difficulty=q.get("difficulty", 1),
                params=q.get("params", {}) or {},
                randomize=q.get("randomize", False),
                correct_answer=q.get("correct_answer", None),
                image=q.get("image", None),
                is_integer=q.get("is_integer", False),
                question_type=q.get("question_type", 0),
                choices=q.get("choices", []) or [],
                exact_match=q.get("exact_match", False)
            )
            out_list.append(qobj)
        questions_data[topic] = out_list

    return questions_data


def get_randomized_question(topic, difficulty=None, questions_path=None):
    """Return (question_text, numeric_answer, question_instance)"""
    questions_map = load_questions_from_file(questions_path)
    questions = questions_map.get(topic, [])
    if not questions:
        return None, None, None

    # Choose by difficulty if possible
    question_obj = None
    if difficulty is not None:
        radius = 0
        while radius <= 10 and question_obj is None:
            candidates = [q for q in questions if q.difficulty == difficulty - radius or q.difficulty == difficulty + radius]
            if candidates:
                question_obj = random.choice(candidates)
            radius += 1
    if question_obj is None:
        question_obj = random.choice(questions)

    question_instance = copy.deepcopy(question_obj)
    q_text, numeric_answer, params = question_instance.generate_question()
    question_instance.randomized_params = params
    return q_text, numeric_answer, question_instance
