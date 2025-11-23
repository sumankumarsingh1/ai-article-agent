import gradio as gr
import json
import os
import time
from datetime import datetime
from llm_loader import load_model
from tools import (
    research_topic,
    create_plan_list,
    draft_all_sections,
    compile_article_and_write,
    create_post_and_write
)

# Ensure outputs directory exists
os.makedirs("outputs", exist_ok=True)

# Load model list
with open("models.json") as f:
    model_list = [m["name"] for m in json.load(f)["models"]]


# -----------------------------
# Step 1: Research & Plan
# -----------------------------
def step_research_and_plan(model_name, topic):
    llm = load_model(model_name)
    research_text, raw_results = research_topic(topic)
    sections, raw_plan = create_plan_list(llm, topic)

    status = f"✅ Found {len(raw_results)} web snippets. Generated {len(sections)} sections."
    sections_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sections)])

    # Return as editable markdown text so user can modify directly
    combined_text = (
        f"## Article Plan for: {topic}\n\n"
        "### Sections (editable)\n"
        f"{sections_text}\n\n"
        "---\n\n"
        f"### Research Notes\n{research_text}"
    )

    return status, combined_text, sections, research_text


# -----------------------------
# Step 2: Generate Drafts
# -----------------------------
def step_generate_drafts(model_name, topic, plan_text, progress=gr.Progress(track_tqdm=False)):
    """
    Generates drafts using the sections extracted from the editable plan text.
    """
    llm = load_model(model_name)

    # Extract sections from plan text (lines starting with digits or bullets)
    lines = [l.strip() for l in plan_text.splitlines() if l.strip()]
    sections = [l.split(".", 1)[1].strip() for l in lines if l[0].isdigit() and "." in l]
    if not sections:
        sections = [l.lstrip("-• ").strip() for l in lines if len(l.split()) > 3][:8]

    logs, drafts = [], []
    start = time.time()

    for i, sec in enumerate(sections):
        sec_start = time.time()
        msg = f"🕒 {datetime.now().strftime('%H:%M:%S')} — Working on section {i+1}/{len(sections)}: {sec}"
        logs.append(msg)
        yield "\n".join(logs), "\n\n".join(drafts)

        draft = draft_all_sections(llm, topic, [sec], "")[0]
        drafts.append(f"### {sec}\n\n{draft}\n\n---")
        elapsed = round(time.time() - sec_start, 1)
        msg = f"✅ {datetime.now().strftime('%H:%M:%S')} — Completed '{sec}' in {elapsed} seconds."
        logs.append(msg)
        yield "\n".join(logs), "\n\n".join(drafts)

    total = round(time.time() - start, 1)
    logs.append(f"✅ All {len(sections)} sections completed in {total} seconds.")
    yield "\n".join(logs), "\n\n".join(drafts)


# -----------------------------
# Step 3: Finalize and Save
# -----------------------------
def step_finalize_and_save(model_name, topic, draft_text):
    llm = load_model(model_name)

    # Split drafts back into sections by delimiter
    parts = [p.strip() for p in draft_text.split("\n---") if p.strip()]
    sections, drafts = [], []

    for p in parts:
        lines = p.splitlines()
        if lines and lines[0].startswith("###"):
            sections.append(lines[0].replace("###", "").strip())
            drafts.append("\n".join(lines[1:]).strip())
        else:
            drafts.append(p)

    article_md, article_path = compile_article_and_write(topic, sections, drafts, outputs_dir="outputs")
    post_text, post_path = create_post_and_write(llm, topic, outputs_dir="outputs")

    status = f"✅ Article saved to {article_path}\n✅ LinkedIn post saved to {post_path}"
    return status, article_md, post_text


# -----------------------------
# UI BUILD
# -----------------------------
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("## 🧠 AI Article Writer Agent (Free Models + Gradio UI)")

    with gr.Row():
        model_dropdown = gr.Dropdown(label="Select Model", choices=model_list, value=model_list[0])
        topic_input = gr.Textbox(label="Topic / Research Query", placeholder="e.g. How AI Agents change product management")

    with gr.Row():
        research_btn = gr.Button("1️⃣ Research & Plan", variant="primary")
        draft_btn = gr.Button("2️⃣ Generate Drafts")
        finalize_btn = gr.Button("3️⃣ Finalize & Save", variant="secondary")

    # Status with more vertical space for logs
    status_box = gr.Textbox(label="🪶 Status / Logs", lines=15, interactive=False)

    # Combined editor for sections + research + drafts
    editable_box = gr.Textbox(label="✍️ Article Workspace (Editable)", lines=25)

    # Final outputs
    final_article = gr.Textbox(label="📄 Final Article", lines=20, interactive=False)
    post_text = gr.Textbox(label="💬 LinkedIn Post", lines=8, interactive=False)

    # Button click wiring
    research_btn.click(
        fn=step_research_and_plan,
        inputs=[model_dropdown, topic_input],
        outputs=[status_box, editable_box, gr.State(), gr.State()]
    )

    draft_btn.click(
        fn=step_generate_drafts,
        inputs=[model_dropdown, topic_input, editable_box],
        outputs=[status_box, editable_box],
        show_progress=True
    )

    finalize_btn.click(
        fn=step_finalize_and_save,
        inputs=[model_dropdown, topic_input, editable_box],
        outputs=[status_box, final_article, post_text]
    )

    gr.Markdown(
        "### 💡 Usage:\n"
        "1️⃣ Click **Research & Plan** → edit section list in the editor.\n"
        "2️⃣ Click **Generate Drafts** → agent fills in sections below.\n"
        "3️⃣ Click **Finalize & Save** → saves `article.md` and `post.md` in `outputs/` folder.\n\n"
        "Use `---` between sections when editing manually."
    )

demo.launch()
