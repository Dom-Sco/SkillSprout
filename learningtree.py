import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
import json
matplotlib.use('TkAgg')

class TopicNode:
    def __init__(self, name, prerequisites=None, completed=False):
        self.name = name
        self.prerequisites = prerequisites if prerequisites else []  # list of prerequisite nodes
        self.completed = completed  # whether this topic has been completed or not

    def add_prerequisite(self, topic_node):
        """Allows adding a prerequisite for this topic"""
        self.prerequisites.append(topic_node)

    def mark_completed(self):
        """Marks this topic as completed"""
        self.completed = True
        print(f"Completed: {self.name}")

    def is_available(self):
        """Check if this topic can be learned (all prerequisites must be completed)"""
        return all(p.completed for p in self.prerequisites)

def load_learning_tree(file_path="learning_tree.json"):
    """Loads the learning tree from a JSON file"""
    with open(file_path, "r") as f:
        data = json.load(f)

    # Create nodes for each topic
    topic_nodes = {}
    for topic in data["topics"]:
        # Create the TopicNode with prerequisites and completed status
        topic_nodes[topic["name"]] = TopicNode(
            name=topic["name"],
            prerequisites=[],  # We'll populate this in the next step
            completed=topic["completed"]
        )

    # Link topics with their prerequisites
    for topic in data["topics"]:
        node = topic_nodes[topic["name"]]
        for prerequisite in topic["prerequisites"]:
            if prerequisite in topic_nodes:
                node.add_prerequisite(topic_nodes[prerequisite])

    return list(topic_nodes.values())


if __name__ == "__main__":
    # Create the topics
    functions = TopicNode("Functions")
    statistics = TopicNode("Statistics", prerequisites=[functions])  # Functions -> Statistics
    differentiation = TopicNode("Differentiation", prerequisites=[functions])  # Functions -> Differentiation
    linear_algebra = TopicNode("Linear Algebra")

    # Advanced topic: Multilayer Perceptrons
    mlp = TopicNode("Multilayer Perceptrons", prerequisites=[statistics, differentiation, linear_algebra])

    # Add prerequisites for each topic
    functions.add_prerequisite(statistics)
    functions.add_prerequisite(differentiation)
    functions.add_prerequisite(linear_algebra)

    # Now let's build the graph using NetworkX

    def build_learning_graph(topics):
        """Build a directed graph for the learning tree"""
        G = nx.DiGraph()  # Create a directed graph
        for topic in topics:
            for prereq in topic.prerequisites:
                # Add an edge from prerequisite to the topic itself
                G.add_edge(prereq.name, topic.name)
        return G

    # List of all topics
    topics = [functions, statistics, differentiation, linear_algebra, mlp]

    # Build the graph
    learning_graph = build_learning_graph(topics)

    # Draw the graph
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(learning_graph)  # Layout for better readability
    nx.draw(learning_graph, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, font_weight="bold", arrows=True)
    plt.title("Learning Tree Graph")
    plt.show()
