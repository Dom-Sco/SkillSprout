from sentence_transformers import SentenceTransformer, util

# Load the model globally (only once)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

SIMILARITY_THRESHOLD = 0.8  # You can tweak this

def check_text_answer(user_answer: str, correct_answer: str, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """
    Returns True if the user's answer is semantically similar to the correct answer.
    """
    if not user_answer or not correct_answer:
        return False

    user_emb = embedding_model.encode(user_answer, convert_to_tensor=True)
    correct_emb = embedding_model.encode(correct_answer, convert_to_tensor=True)

    similarity = util.pytorch_cos_sim(user_emb, correct_emb).item()
    return similarity >= threshold

def get_text_similarity(user_answer: str, correct_answer: str) -> float:
    """
    Returns the cosine similarity score (0-1) between user answer and correct answer.
    """
    if not user_answer or not correct_answer:
        return 0.0

    user_emb = embedding_model.encode(user_answer, convert_to_tensor=True)
    correct_emb = embedding_model.encode(correct_answer, convert_to_tensor=True)

    return util.pytorch_cos_sim(user_emb, correct_emb).item()
