from __future__ import annotations
import os, json, random, re
from typing import Dict, Any, List
from openai import OpenAI
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------
# 1) Load FairytaleQA dataset
# ---------------------------------------------------------
def load_fairytale() -> Any:
    try:
        ds = load_dataset("GEM/FairytaleQA", trust_remote_code=False)
        return ds
    except Exception as e:
        print("❌ Could not load FairytaleQA dataset:", e)
        return None

# ---------------------------------------------------------
# 2) Pick full story (all fragments)
# ---------------------------------------------------------
def pick_full_story(ds) -> Dict[str, Any]:
    splits = list(ds.keys())
    chosen_split = random.choice(splits)
    rows = ds[chosen_split]

    story_names = list({r["story_name"] for r in rows})
    story_name = random.choice(story_names)

    fragments = [r["content"].strip() for r in rows if r["story_name"] == story_name]

    return {"story_name": story_name, "fragments": fragments}

# ---------------------------------------------------------
# 3) Ask GPT to reorder story perfectly
# ---------------------------------------------------------
def reorder_with_gpt(story_name: str, fragments: List[str]) -> str:
    prompt = f"""
You are an expert in reconstructing narrative order.
Reorder the following story fragments into the correct logical sequence 
(beginning → middle → end).

Rules:
- Do NOT rewrite or paraphrase any sentences.
- Only reorder fragments.
- Remove duplicated segments.
- Output ONLY the final clean full story as continuous text.

Story name: {story_name}

Fragments:
{fragments}
"""

    res = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )
    story_text = res.output_text.strip()
    return story_text

# ---------------------------------------------------------
# 4) Sentence splitter
# ---------------------------------------------------------
def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r'(?<=[.!?])\s+', text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts

# ---------------------------------------------------------
# 5) Save files (JSON + TXT)
# ---------------------------------------------------------
def save_story_files(story_name: str, story_text: str, sentences: List[str]) -> Dict[str, str]:
    folder = os.path.join(os.getcwd(), "server", "stories")
    os.makedirs(folder, exist_ok=True)

    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)

    json_path = os.path.join(folder, f"{safe_name}.json")
    txt_path = os.path.join(folder, f"{safe_name}.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "story_name": story_name,
            "sentence_count": len(sentences),
            "sentences": sentences,
            "story_text": story_text
        }, f, indent=2, ensure_ascii=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(story_text)

    return {"json": json_path, "txt": txt_path}

# ---------------------------------------------------------
# 6) Main API
# ---------------------------------------------------------
def get_or_build_story() -> Dict[str, Any]:
    ds = load_fairytale()
    if ds is None:
        return {
            "story_name": "Fallback Story",
            "story_text": "Dataset unavailable.",
            "sentences": ["Dataset unavailable."],
            "sentence_count": 1
        }

    block = pick_full_story(ds)
    name = block["story_name"]
    fragments = block["fragments"]

    print(f"📘 Rebuilding story: {name} ({len(fragments)} fragments)")

    story_text = reorder_with_gpt(name, fragments)
    sentences = split_sentences(story_text)

    paths = save_story_files(name, story_text, sentences)
    print(f"💾 Saved: {paths}")

    return {
        "story_name": name,
        "story_text": story_text,
        "sentences": sentences,
        "sentence_count": len(sentences)
    }

# ---------------------------------------------------------
# 7) Local test
# ---------------------------------------------------------
if __name__ == "__main__":
    story = get_or_build_story()
    print("\n=========================================")
    print("Final Story Name:", story["story_name"])
    print("Total Sentences:", story["sentence_count"])
    print("=========================================")
    print(story["story_text"])

# ---------------------------------------------------------
# 8) REQUIRED by data_retriever → build_story_block
# ---------------------------------------------------------
def build_story_block() -> Dict[str, Any]:
    ds = load_fairytale()
    if ds is None:
        return {
            "story_name": "Fallback Story",
            "story_text": "Dataset unavailable.",
            "sentences": ["Dataset unavailable."],
            "sentence_count": 1
        }

    block = pick_full_story(ds)
    name = block["story_name"]
    fragments = block["fragments"]

    print(f"[StoryConstructor] Building fresh story: {name}")

    story_text = reorder_with_gpt(name, fragments)
    sentences = split_sentences(story_text)

    return {
        "story_name": name,
        "story_text": story_text,
        "sentences": sentences,
        "sentence_count": len(sentences)
    }
