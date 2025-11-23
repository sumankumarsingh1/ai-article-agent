from langchain_core.language_models.llms import LLM

class OpenRouterLLM(LLM):
    ...
    def _call(self, prompt, **kwargs):
        return self.invoke(prompt)
    
    @property
    def _identifying_params(self):
        return {"model": self.model, "base_url": self.base_url}
    
    @property
    def _llm_type(self):
        return "openrouter"