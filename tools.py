import os
import re
from datetime import datetime
import time
from typing import Any
from ddgs import DDGS


def research_topic(topic, max_results=5):
    """Return a short concatenated research summary (string) and raw search results (list)."""
    results = []
    try:
        ddgs = DDGS()
        for r in ddgs.text(topic, max_results=max_results):
            results.append(r.get("body", "") or r.get("text", ""))
    except Exception:
        results = []
    research_text = "\n\n".join(results)
    return research_text, results


def get_clean_text(resp: Any) -> str:
    """Unified response cleaner for all LLM types."""
    if hasattr(resp, "content") and isinstance(resp.content, str):
        text = resp.content
    elif isinstance(resp, dict):
        text = resp.get("content", "") or str(resp)
    else:
        text = str(resp)
    return text.strip()


def create_plan_list(llm, topic, max_sections=8):
    """
    Ask the LLM to return a numbered list of section titles / outline.
    Returns a Python list of clean strings (section titles).
    """
    prompt = (
        f"Create a concise, numbered outline for an in-depth LinkedIn article about: '{topic}'.\n"
        "Return only the numbered list of section titles (no extra commentary). "
        "Include 4-8 sections that cover what, why, how, and future trends."
    )

    raw_response = llm.invoke(prompt)
    raw_text = raw_response.content if hasattr(raw_response, "content") else str(raw_response)

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    sections = []
    for line in lines:
        cleaned = line
        if "." in cleaned and cleaned[0].isdigit():
            cleaned = cleaned.split(".", 1)[1].strip()
        elif ")" in cleaned and cleaned[0].isdigit():
            cleaned = cleaned.split(")", 1)[1].strip()
        elif cleaned.startswith("- "):
            cleaned = cleaned[2:].strip()

        # 🧹 Clean extra markup or artifacts
        cleaned = re.sub(r"<\/?s>", "", cleaned)  # remove <s> or </s>
        cleaned = re.sub(r"[*_`]+", "", cleaned)  # remove markdown artifacts
        cleaned = cleaned.strip()

        if cleaned:
            sections.append(cleaned)
        if len(sections) >= max_sections:
            break

    if not sections:
        sections = lines[:max_sections]

    return sections, raw_text


def draft_section(llm, topic, section_title, research_text=None):
    """Return a draft (string) for a single section."""
    prompt = (
        f"You are writing a LinkedIn article section. Topic: '{topic}'.\n"
        f"Section: '{section_title}'.\n"
    )
    if research_text:
        prompt += (
            "Use the following research notes to support the section. "
            "If research is not relevant, write an original, well-structured section.\n\n"
            f"Research notes:\n{research_text}\n\n"
        )
    prompt += "Write a professional, ~2-4 paragraph section suitable for LinkedIn, with a short summary sentence at the start."

    resp = llm.invoke(prompt)
    return get_clean_text(resp)


def draft_all_sections(llm, topic, sections, research_text=None, progress_callback=None):
    """Draft all sections and return list of drafts aligned with `sections`."""
    drafts = []
    for i, sec in enumerate(sections):
        start_time = time.time()
        if progress_callback:
            progress_callback(i, sec, f"🟡 Working on section {i+1}/{len(sections)}: {sec}")
        try:
            d = draft_section(llm, topic, sec, research_text)
        except Exception as e:
            d = f"⚠️ Error drafting section: {sec}\n{e}"
        elapsed = round(time.time() - start_time, 1)
        if progress_callback:
            progress_callback(i, sec, f"✅ Completed '{sec}' in {elapsed} seconds.\n")
        drafts.append(d)
    return drafts


def compile_article_and_write(topic, outline_list, draft_list, outputs_dir="outputs"):
    """Compile article markdown and return the final string."""
    os.makedirs(outputs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    safe_topic = re.sub(r"[^A-Za-z0-9_]+", "_", topic.strip().replace(" ", "_"))
    filename = f"{safe_topic}_article_{timestamp}.md"
    path = os.path.join(outputs_dir, filename)

    header = f"# {topic.strip()}\n\n"
    outline_md = "## Outline\n\n" + "\n".join([f"- {s.strip()}" for s in outline_list]) + "\n\n"

    content_parts = []
    for title, draft in zip(outline_list, draft_list):
        clean_title = title.strip()
        body = draft.strip()

        # Remove repeated title inside content
        pattern = re.compile(re.escape(clean_title), re.IGNORECASE)
        body = pattern.sub("", body, count=1).strip(" :.-")
        content_parts.append(f"### {clean_title}\n\n{body}\n")

    article_md = header + outline_md + "\n".join(content_parts).strip() + "\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(article_md)

    return article_md, path


def create_post_and_write(llm, topic, sections=None, outputs_dir="outputs"):
    """Generates a LinkedIn post summary based on the article’s content."""
    os.makedirs(outputs_dir, exist_ok=True)

    context_text = ""
    if sections:
        context_text = "\n\n".join([f"Section {i+1}: {s}" for i, s in enumerate(sections)])

    prompt = f"""
    You are an expert LinkedIn content writer.
    Write a short, engaging LinkedIn post summarizing the following article about "{topic}".
    The post should:
    - Capture key insights and highlights.
    - Encourage professionals to read or reflect.
    - Sound conversational but professional.

    Article context:
    {context_text}
    """

    post_response = llm.invoke(prompt)
    post_text = get_clean_text(post_response)

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    safe_topic = re.sub(r"[^A-Za-z0-9_]+", "_", topic.strip().replace(" ", "_"))
    filename = f"{safe_topic}_post_{timestamp}.md"
    filepath = os.path.join(outputs_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(post_text)

    return post_text, filepath
