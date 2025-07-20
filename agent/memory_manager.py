import faiss
import os
import pickle
import re
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

os.makedirs("memory", exist_ok=True)

# Load model (CPU-safe)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
embedder.to("cpu")

dimension = 384
INDEX_FILE = "memory/faiss.index"
META_FILE = "memory/meta.pkl"
LOG_FILE = "memory/memory_log.txt"

# Load or create FAISS index
if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
else:
    index = faiss.IndexFlatL2(dimension)

# Load metadata
if os.path.exists(META_FILE):
    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)
else:
    metadata = []

print(f"[🧠] Loaded {len(metadata)} memory records.")


def embed_text(text: str):
    return embedder.encode([text])[0]


def clean_result_text(text: str) -> str:
    text = re.sub(r"\n\s*\$\s*", " ", text)
    text = re.sub(r"/[^ ]+/", "[PATH]", text)
    text = re.sub(r"Traceback.*", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text)
    lines = text.strip().splitlines()
    return "\n".join(lines[:5]).strip()[:300]


def store_memory(task: str, command: str, result: str, success: bool = True, parent_task: str = None):
    if not result.strip():
        return

    vector = embed_text(task)
    index.add(vector.reshape(1, -1))

    cleaned_result = clean_result_text(result)
    entry = {
        "task": task,
        "command": command,
        "result": cleaned_result,
        "success": success,
        "parent": parent_task,
    }
    metadata.append(entry)
    persist_memory()
    log_to_file(entry)


def retrieve_similar_tasks(task: str, k=3):
    if len(metadata) == 0:
        return []

    query_vector = embed_text(task).reshape(1, -1)
    distances, indices = index.search(query_vector, k * 2)

    filtered = []
    seen_tasks = set()

    for i in indices[0]:
        if i < len(metadata):
            m = metadata[i]
            if m["success"] and m["task"] not in seen_tasks:
                filtered.append(m)
                seen_tasks.add(m["task"])
        if len(filtered) >= k:
            break

    return filtered


def is_continuation_semantic(new_task: str, threshold=0.7):
    """
    Determine if this task is likely a continuation of a previous task.
    Returns the best-matching previous task dict or None.
    """
    if not metadata:
        return None

    new_vec = embed_text(new_task)
    best_match = None
    best_score = -1

    for m in reversed(metadata):  # prioritize recent
        old_vec = embed_text(m["task"])
        sim = np.dot(new_vec, old_vec) / (np.linalg.norm(new_vec) * np.linalg.norm(old_vec))
        if sim > best_score:
            best_score = sim
            best_match = m

    if best_score >= threshold:
        return best_match
    return None


def persist_memory():
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)


def log_to_file(entry: dict):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    status = "SUCCESS" if entry["success"] else "FAILED"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{status}]\n")
        f.write(f"Task   : {entry['task']}\n")
        f.write(f"Command: {entry['command']}\n")
        f.write(f"Result : {entry['result']}\n")
        if entry.get("parent"):
            f.write(f"Parent : {entry['parent']}\n")
        f.write("-" * 50 + "\n")
