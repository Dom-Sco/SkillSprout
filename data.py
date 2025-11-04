class UserData:
    def __init__(self):
        self.time_on_question = 0.0  # Time spent on the question
        self.difficulty = None       # Question difficulty (could be an int, float, or string)
        self.topic = None            # Topic of the question
        self.submitted_answer = None # The answer the user submitted
        self.correct_answer = None   # The actual correct answer
        self.correct = False         # Whether the answer was correct (True/False)
        self.correct_streak = 0      # Number of consecutive correct answers

    def update(self, time_on_question, difficulty, topic, submitted_answer, correct_answer, correct):
        self.time_on_question = time_on_question
        self.difficulty = difficulty
        self.topic = topic
        self.submitted_answer = submitted_answer
        self.correct_answer = correct_answer
        self.correct = correct

        # Update streak based on correctness
        if correct:
            self.correct_streak += 1
        else:
            self.correct_streak = 0

    def to_dict(self):
        return {
            "time_on_question": self.time_on_question,
            "difficulty": self.difficulty,
            "topic": self.topic,
            "submitted_answer": self.submitted_answer,
            "correct_answer": self.correct_answer,
            "correct": self.correct,
            "correct_streak": self.correct_streak
        }
