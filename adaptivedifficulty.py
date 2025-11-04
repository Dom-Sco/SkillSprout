import numpy as np
import csv
import time
import random

class AdaptiveDifficultyQlearning:
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.9, epsilon_decay=0.995, epsilon_min=0.1, csv_file='user_data.csv'):
        # Initialize parameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.csv_file = csv_file
        
        # Initialize the Q-table (100 unique states and 10 possible difficulties)
        self.q_table = np.zeros((100, 10))  # Assuming 100 possible states, 10 difficulty levels (0-9)
        self.state = 0  # Initial state (this will change based on user progress)
        self.reset_state()  # Initialize user-specific state

    def reset_state(self):
        """Reset user-specific state (correct answers, streaks, etc.)."""
        self.state = {
            'correct_streak': 0,
            'total_correct': 0,
            'time_spent': 0,  # Start with 0 time
            'total_questions': 0
        }

    def choose_action(self):
        """Select an action using epsilon-greedy policy."""
        if random.uniform(0, 1) < self.epsilon:
            # Exploration: choose a random action (difficulty level)
            action = random.randint(0, 9)
        else:
            # Exploitation: choose the best action (difficulty level)
            action = np.argmax(self.q_table[self.state['total_questions']])
        
        return action

    def update_q_table(self, action, reward, next_state):
        """Update the Q-table using the Q-learning formula."""
        current_q_value = self.q_table[self.state['total_questions'], action]
        max_future_q = np.max(self.q_table[next_state['total_questions']])
        
        # Q-learning formula
        new_q_value = current_q_value + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q_value)
        self.q_table[self.state['total_questions'], action] = new_q_value

        # Update state for next iteration
        self.state = next_state

    def calculate_reward(self, correct, time_spent, streak, question_type=0):
        """Reward function based on correctness, time, streak, and type."""
        base_reward = 10 if correct else -5
        time_bonus = max(0, 10 - time_spent)
        streak_bonus = streak * 1.5

        # Optional: give slightly higher reward for correct numeric answers
        type_bonus = 2 if (correct and question_type == 0) else 0

        return base_reward + time_bonus + streak_bonus + type_bonus


    def log_data(self, difficulty, correct, time_spent, streak):
        """Log data into CSV file for tracking."""
        # Define the CSV file name
        file_name = self.csv_file

        # Define the column headers (if the file is new)
        fieldnames = [
            'time_on_question', 'difficulty', 'topic',
            'question_type', 'submitted_answer', 'correct_answer',
            'correct', 'correct_streak'
        ]

        # Check if the file exists
        file_exists = os.path.isfile(file_name)

        # Open the CSV file in append mode
        with open(file_name, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # If file does not exist, write the header first
            if not file_exists:
                writer.writeheader()

            # Append the user data as a new row
            writer.writerow({
                'difficulty': difficulty + 1,  # Store difficulty 1-10
                'correct': 1 if correct else 0,  # Store correct answer as 1/0
                'time_on_question': time_spent,
                'submitted_answer': 'user_answer',  # Placeholder, change accordingly
                'correct_answer': 'correct_answer',  # Placeholder, change accordingly
                'correct_streak': streak
            })

    def load_csv(self):
        """Load CSV data into a list, with error handling for invalid rows."""
        data = []
        try:
            with open(self.csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        difficulty = int(row.get('difficulty', 0))
                        correct = int(row.get('correct', 0)) == 1
                        time_spent = float(row.get('time_on_question', 0))
                        streak = int(row.get('correct_streak', 0))
                        # You could also read question_type here if needed later:
                        # qtype = int(row.get('question_type', 0))

                        data.append((difficulty, correct, time_spent, streak))
                    except (ValueError, TypeError):
                        print(f"Skipping invalid row: {row}")
        except FileNotFoundError:
            print("CSV file not found, starting a new log.")
        return data

    def train_with_csv_data(self):
        """Train the model with existing data from the CSV."""
        data = self.load_csv()
        
        for row in data:
            difficulty, correct, time_spent, streak = row

            # Calculate reward based on the data
            reward = self.calculate_reward(correct, time_spent, streak)
            
            # Simulate user state update
            next_state = self.state.copy()
            next_state['total_questions'] += 1
            if correct:
                next_state['total_correct'] += 1
                next_state['correct_streak'] += 1
            else:
                next_state['correct_streak'] = 0
            
            # Update Q-table using the state, action, and reward
            self.update_q_table(difficulty, reward, next_state)
            
            # Decay epsilon for exploration vs exploitation
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay

        print("Training complete with existing CSV data.")

if __name__ == "__main__":
    # Initialize the Q-learning agent
    agent = AdaptiveDifficultyQlearning(csv_file='user_data.csv')

    # Train the model with the existing data in CSV
    agent.train_with_csv_data()

    # After training, print out the Q-table for inspection
    print(agent.q_table)

    # Optionally, you can load and check logged data
    print(agent.load_csv())
