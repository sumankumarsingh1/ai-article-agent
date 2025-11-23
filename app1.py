import gradio as gr
from llm_loader import load_model
from tools import research_topic, create_plan, draft_sections, compile_article, create_post
import json

with open("models.json") as f:
    model_list = [m["name"] for m in json.load(f)["models"]]

def run_agent(model_name, topic):
    llm = load_model(model_name)
    research = research_topic(topic)
    plan = create_plan(llm, topic)
    drafts = draft_sections(llm, plan)
    compile_article(topic, plan, drafts)
    create_post(llm, topic)
    return f"✅ Article and LinkedIn post created!\n\nSee: article.md & post.md"

demo = gr.Interface(
    fn=run_agent,
    inputs=[gr.Dropdown(choices=model_list, label="Select Model"),
            gr.Textbox(label="Enter Topic")],
    outputs="text",
    title="AI Article Writer Agent"
)

demo.launch()
