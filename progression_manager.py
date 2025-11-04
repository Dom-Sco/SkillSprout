import json
from typing import Dict, List, Tuple

class ProgressionManager:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.topics = self._load_topics()

    # --------------------
    # File I/O
    # --------------------
    def _load_topics(self) -> Dict[str, dict]:
        with open(self.json_path, "r") as f:
            data = json.load(f)
        return {t["name"]: t for t in data["topics"]}

    def save_topics(self):
        with open(self.json_path, "w") as f:
            json.dump({"topics": list(self.topics.values())}, f, indent=2)

    # --------------------
    # Mastery logic
    # --------------------
    def is_topic_mastered(self, topic_name: str, stats: dict) -> bool:
        """Check if a topic is mastered based on JSON-defined conditions and user stats."""
        topic = self.topics.get(topic_name)
        if not topic:
            return False

        cond = topic.get("conditions", {})
        min_q = cond.get("min_questions", 5)
        min_acc = cond.get("min_accuracy", 0.8)
        min_streak = cond.get("min_streak", 3)

        attempts = stats.get("n_attempts", 0)
        correct = stats.get("n_correct", 0)
        avg_sim = stats.get("avg_similarity", 0.0)
        streak = stats.get("streak", 0)

        if attempts < min_q:
            return False

        accuracy = correct / max(attempts, 1)
        similarity = avg_sim if avg_sim > 0 else accuracy

        return (
            accuracy >= min_acc
            and similarity >= min_acc
            and streak >= min_streak
        )

    # --------------------
    # Prerequisite & unlocking
    # --------------------
    def can_unlock(self, topic_name: str) -> bool:
        topic = self.topics.get(topic_name)
        if not topic:
            return False
        prereqs = topic.get("prerequisites", [])
        return all(self.topics[p]["completed"] for p in prereqs)

    def unlock_available_topics(self) -> List[str]:
        available = []
        for name, info in self.topics.items():
            if not info["completed"] and self.can_unlock(name):
                available.append(name)
        return available

    def mark_topic_completed(self, topic_name: str):
        if topic_name in self.topics:
            self.topics[topic_name]["completed"] = True

    # --------------------
    # Main progression update
    # --------------------
    def check_and_update_progress(self, topic_stats: Dict[str, dict]) -> Tuple[List[str], List[str]]:
        """
        topic_stats: dict[topic_name -> stats]
        Each stats dict must include: n_attempts, n_correct, avg_similarity, streak

        Returns: (newly_mastered_topics, newly_unlocked_topics)
        """
        newly_mastered = []

        for topic_name, stats in topic_stats.items():
            if self.is_topic_mastered(topic_name, stats):
                if not self.topics[topic_name]["completed"]:
                    self.mark_topic_completed(topic_name)
                    newly_mastered.append(topic_name)

        newly_unlocked = self.unlock_available_topics()
        self.save_topics()

        return newly_mastered, newly_unlocked
