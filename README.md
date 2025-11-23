# 🧠 AI Article Agent  
A hands-on project to learn how to use Local and Cloud LLMs to generate high-quality written content.

---

## 📌 Project Overview

The **AI Article Agent** is a beginner-friendly project designed for students learning how to work with Large Language Models (LLMs).  
This project demonstrates how AI can:

- Research a topic  
- Create a structured outline  
- Generate a complete article  
- Produce a short social media post summarizing the content  

It supports both:

- 🖥 Local LLMs (via **Ollama**)  
- 🌐 Cloud-based LLMs (via **OpenRouter.ai**)  

This makes it ideal for learning hybrid AI application development.

---

## 🚀 Features

✔️ Works with multiple LLM providers  
✔️ Fully automated article writing workflow  
✔️ Search-assisted topic research using DuckDuckGo  
✔️ Generates:

- 📝 Full-length article  
- 📌 Short summary post  
- 📁 Outputs saved locally  

✔️ Built for education and experimentation

---

## 🛠️ Prerequisites

### 1️⃣ Install Ollama

Download from:

👉 https://ollama.com/download  

Pull at least one model, for example:

```bash
ollama pull llama3
```

### 2️⃣ Create a .env file with your OpenRouter Key

Create a file named .env in the project folder and add:

```bash
OPENROUTER_API_KEY=your_api_key_here
```

📝 This is optional — only needed if you want to use remote cloud LLMs.


### 3️⃣ (Optional) Update models.json

You can configure which models the app will use.

Example block to add:
```bash
    {
      "name": "mistral (OpenRouter)",
      "type": "openrouter",
      "params": {
        "model": "mistralai/mistral-7b-instruct:free",
        "base_url": "https://openrouter.ai/api/v1"
      }
    },   
```

### 📦 Installation

Run the following commands:
```bash
git clone <repo-url>
cd ai-article-agent
pip install -r requirements.txt
```

### ▶️ Running the Application

Once installed, start the program:

```bash
python app.py
```



The system will guide you through:

1. Selecting a topic

2. Choosing a model (local or cloud)

3. Generating content

The agent will then:

* Research the topic

* Create an outline

* Generate a full article

* Create a short promotional post

* Save everything inside the output/ folder

📁 Project Structure
```bash
ai-article-agent/
│
├── app1.py                # Main executable workflow
├── tools.py               # Functions for research + content generation
├── llm_loader.py          # Handles model loading (local + cloud)
├── models.json            # Model configuration file
├── outputs/                # Folder storing generated content
└── requirements.txt       # Project dependencies

```

🎓 What You Will Learn

By completing this project, you will gain hands-on experience in:

* Using LLMs programmatically from Python

* Switching between local and cloud models

* Automating content generation workflows

* Integrating search-assisted research

* Building AI-powered productivity tools

* Saving structured output for reuse

### ✨ Optional Future Enhancements
| Feature | Difficulty	| Status |
| ------- | ----------- | ------ |
| Web UI with Gradio | ⭐⭐ | Planned |
| SEO keyword extraction | ⭐⭐⭐ | Optional |
| Banner image generation via Stable Diffusion | ⭐⭐⭐⭐ | Optional |
| Text-to-speech article narration	| ⭐⭐ | Optional


### 🤝 Contributing
* This is a learning-focused project — feel free to fork, improve, and create pull requests.
* Suggestions and enhancements are always welcome!
* Share with us what good learnings you had.

### 📄 License

Licensed under the MIT License — free to use, modify, and share.