# app.py
import gradio as gr
import json
import os
from llm_loader import load_model
from tools import (
    research_topic,
    create_plan_list,
    draft_all_sections,
    compile_article_and_write,
    create_post_and_write
)
import time
from datetime import datetime


# ensure outputs folder
os.makedirs("outputs", exist_ok=True)

# load model choices from models.json
with open("models.json") as f:
    model_list = [m["name"] for m in json.load(f)["models"]]


def step_research_and_plan(model_name, topic):
    """
    Called when user clicks 'Research & Plan'
    Returns: status message, research text, list of section titles, raw_plan_text
    We'll store model_name and topic in state on the client side.
    """
    llm = load_model(model_name)
    research_text, raw_results = research_topic(topic)
    sections, raw_plan = create_plan_list(llm, topic)
    status = f"Found {len(raw_results)} search snippets. Generated {len(sections)} sections."
    # return: status, research, sections joined as markdown, raw_plan (for debugging)
    sections_md = "\n".join([f"- {s}" for s in sections])
    return status, research_text, sections, raw_plan, sections_md


def step_generate_drafts(model_name, topic, sections, research_text, progress=gr.Progress(track_tqdm=False)):
    """
    Called when user clicks 'Generate Drafts'
    Returns list of drafts (list), and status string.
    """
    llm = load_model(model_name)
    logs = []

    def progress_callback(i, title, msg):
        logs.append(msg)
        progress(i / len(sections), desc=msg)  # show in progress bar
        # append to live log (this will show in the status box)
        yield "\n".join(logs)

    # we can’t stream directly from progress_callback easily, so simpler approach:
    start = time.time()
    drafts = []
    for i, sec in enumerate(sections):
        sec_start = time.time()
        ## msg = f"🟡 Working on section {i+1}/{len(sections)}: {sec}"
        msg = f"🕒 {datetime.now().strftime('%H:%M:%S')} — Working on section {i+1}/{len(sections)}: {sec}"
        logs.append(msg)
        yield "\n".join(logs), drafts  # intermediate update

        d = draft_all_sections(llm, topic, [sec], research_text)[0]
        drafts.append(d)
        elapsed = round(time.time() - sec_start, 1)
        # msg = f"✅ Completed '{sec}' in {elapsed} seconds."
        msg = f"✅ {datetime.now().strftime('%H:%M:%S')} — Completed '{sec}' in {elapsed} seconds."
        logs.append(msg)
        yield "\n".join(logs), drafts

    total = round(time.time() - start, 1)
    logs.append(f"✅ All {len(sections)} sections completed in {total} seconds.")
    yield "\n".join(logs), drafts

def step_finalize_and_save(model_name, topic, sections, drafts):
    """
    Persist edits, compile article, create post.
    Returns paths and messages.
    """
    llm = load_model(model_name)
    article_md, article_path = compile_article_and_write(topic, sections, drafts, outputs_dir="outputs")
    post_text, post_path = create_post_and_write(llm, topic, outputs_dir="outputs")
    return (
        f"Article saved to {article_path}",
        f"Post saved to {post_path}",
        article_md,
        post_text
    )


# Build the Gradio app
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("## AI Article Writer Agent — Multi-step (Research → Draft → Edit → Save)")

    with gr.Row():
        model_dropdown = gr.Dropdown(label="Select Model", choices=model_list, value=model_list[0])
        topic_input = gr.Textbox(label="Topic / Research Query", placeholder="e.g. 'How AI Agents change product management'")

    with gr.Row():
        research_btn = gr.Button("Research & Plan", variant="primary")
        gen_drafts_btn = gr.Button("Generate Drafts", interactive=True)
        finalize_btn = gr.Button("Finalize & Save", variant="secondary")

    # Status and intermediate displays
    status_box = gr.Textbox(label="Status", interactive=False)
    research_md = gr.Textbox(label="Research notes (read-only)", lines=8, interactive=False)
    raw_plan_box = gr.Textbox(label="Raw plan text (LLM output)", lines=6, interactive=False)
    sections_md = gr.Markdown("", visible=True)

    # We'll create a dynamic area to hold editable textboxes for each section
    drafts_container = gr.Column()  # empty container to be populated programmatically

    # Hidden states
    sections_state = gr.State([])   # holds list of section titles
    drafts_state = gr.State([])     # holds list of draft strings
    topic_state = gr.State("")      # holds current topic
    model_state = gr.State(model_list[0])

    # ---- callbacks ----
    def research_clicked(model_name, topic):
        if not topic or not topic.strip():
            return "Please enter a topic", "", [], "", ""
        status, research_text, sections, raw_plan, sections_md_text = step_research_and_plan(model_name, topic)
        return status, research_text, raw_plan, sections_md_text, sections

    research_btn.click(
        fn=research_clicked,
        inputs=[model_dropdown, topic_input],
        outputs=[status_box, research_md, raw_plan_box, sections_md, sections_state]
    )

    # helper to render the editable textboxes for drafts
    def render_draft_textboxes(sections, drafts):
        # create a dict mapping id->value for use in update
        # We'll create up to len(sections) textboxes in the column.
        children = []
        textboxes = []
        for i, title in enumerate(sections):
            # For each section create a heading and a multiline textbox prefilled with draft (if provided)
            tb = gr.Textbox(label=f"{i+1}. {title}", lines=8, value=(drafts[i] if drafts and i < len(drafts) else ""))
            children.append(tb)
            textboxes.append(tb)
        return textboxes

    # generate drafts button callback: will call step_generate_drafts and then populate the drafts_container
    def generate_drafts_click(model_name, topic, sections):
        if not sections:
            return "No sections found. First run Research & Plan.", [], "No drafts"
        drafts, status = step_generate_drafts(model_name, topic, sections, research_md.value if research_md.value else "")
        # return drafts to drafts_state, and status
        return drafts, status

    gen_drafts_btn.click(
        fn=step_generate_drafts,
        inputs=[model_dropdown, topic_input, sections_state, research_md],
        outputs=[status_box, drafts_state],
        show_progress=True
    )

    # After drafts_state is populated, we need to display editable textboxes.
    # We'll provide a button to "Load Drafts into Editor".
    load_editor_btn = gr.Button("Load Drafts into Editor")

    def load_editor(sections, drafts):
        # returns a tuple: a list of textbox components (we cannot create components dynamically in outputs),
        # instead we return a big Markdown that instructs user to edit drafts below and we'll wire each textbox below to use drafts_state as initial values.
        # Simpler approach: render a single Markdown + one large editable textarea containing concatenated drafts separated by clear delimiters
        # BUT requirement is per-section editing. So we will build a single multi-part textarea prefilled with markers.
        content = ""
        for i, title in enumerate(sections):
            content += f"### {i+1}. {title}\n\n"
            content += (drafts[i] if drafts and i < len(drafts) else "") + "\n\n---\n\n"
        return content

    # We will use a single big editable editor (editable_drafts_editor) to show all drafts split by '---' markers.
    editable_drafts_editor = gr.Textbox(label="Edit drafts (each section separated by ---)", lines=20, placeholder="Edit drafts here...")

    load_editor_btn.click(
        fn=load_editor,
        inputs=[sections_state, drafts_state],
        outputs=[editable_drafts_editor]
    )

    # When user clicks 'Finalize & Save' split edited content back into per-section drafts and save.
    def finalize_click(model_name, topic, sections, edited_all):
        if not sections:
            return "No sections available to finalize.", "", "", ""
        # split edited_all by the delimiter '---' and map to sections
        parts = [p.strip() for p in edited_all.split("\n---\n") if p.strip()]
        # if the parts look like they include headings (### n. Title) remove heading lines
        cleaned = []
        for p in parts:
            lines = p.splitlines()
            # drop leading heading lines starting with '#'
            while lines and lines[0].strip().startswith("#"):
                lines = lines[1:]
            cleaned.append("\n".join(lines).strip())
        # ensure same length as sections
        final_drafts = []
        for i in range(len(sections)):
            if i < len(cleaned) and cleaned[i]:
                final_drafts.append(cleaned[i])
            else:
                final_drafts.append("")  # empty if missing
        # compile and write
        article_msg, post_msg, article_md, post_text = step_finalize_and_save(model_name, topic, sections, final_drafts)
        return article_msg, post_msg, article_md, post_text

    finalize_btn.click(
        fn=finalize_click,
        inputs=[model_dropdown, topic_input, sections_state, editable_drafts_editor],
        outputs=[status_box, status_box, gr.Textbox(label="Final Article Preview", lines=20), gr.Textbox(label="LinkedIn Post", lines=8)]
    )

    # Helpful hint
    gr.Markdown("**Workflow:** 1) Research & Plan → 2) Generate Drafts → 3) Load Drafts → Edit → 4) Finalize & Save\n\n"
                "Use `---` on its own line to separate drafts when editing in the editor.")

demo.launch()
