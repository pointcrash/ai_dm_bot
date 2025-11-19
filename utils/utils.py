import os
from pathlib import Path


def get_path_to_simple_history_file(chat_id: int) -> Path:
    folder = "simple_histories/{chat_id}".format(chat_id=chat_id)
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"simple_history_{chat_id}.txt")
    return Path(filename)