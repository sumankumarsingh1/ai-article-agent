# tools.py
from ddgs import DDGS

def research_topic(topic):
    results = DDGS().text(topic, max_results=5)
    return "\n".join([r["body"] for r in results])

def create_plan(llm, topic):
    prompt = f"Create an outline for a LinkedIn article about '{topic}'. Include sections answering what, why, how, and future trends."
    return llm.invoke(prompt)

def draft_sections(llm, plan):
    sections = plan.split("\n")
    drafts = []
    for sec in sections:
        if sec.strip():
            draft = llm.invoke(f"Write a detailed section for: {sec}")
            drafts.append(f"## {sec}\n{draft}")
    return "\n\n".join(drafts)

def compile_article(topic, plan, content):
    article = f"# {topic}\n\n{plan}\n\n{content}"
    with open("outputs/article.md", "w", encoding="utf-8") as f:
        f.write(article)

def create_post(llm, topic):
    prompt = f"Write a short LinkedIn post to announce a new article about {topic}. Keep it under 300 words."
    post = llm.invoke(prompt)
    with open("outputs/post.md", "w", encoding="utf-8") as f:
        f.write(post)
