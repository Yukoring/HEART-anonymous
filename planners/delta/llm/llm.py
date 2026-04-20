"""
LLM Client Interfaces for DELTA

Two client implementations:
  - GPT: Original DELTA Azure OpenAI client (kept for reference)
  - OpenAIModel: HEART addition using standard OpenAI API (used in experiments)
"""

from copy import deepcopy
import os
import tiktoken
from dotenv import load_dotenv

# ---------- Optional imports for local models (Llama, Gemma) ----------
# Not required when using OpenAI API only.
try:
    import torch
    from transformers import AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
# ----------------------------------------------------------------------

load_dotenv()
MAX_NEW_TOKENS = 16384


class LLMBase:
    def __init__(self, temp: float = 0., top_p: float = 1.):
        self.temperature = temp
        self.top_p = top_p
        self.prompt_chain = []
        self.total_tokens = 0  # Accumulated tokens across all queries in this LLM instance
        if TRANSFORMERS_AVAILABLE:
            torch.cuda.empty_cache()

    def reset(self):
        self.prompt_chain = []
        self.total_tokens = 0
        if TRANSFORMERS_AVAILABLE:
            torch.cuda.empty_cache()

    def count_tokens(self, string: str):
        pass

    def init_prompt_chain(self, content: str, prompt: str):
        pass

    def update_prompt_chain(self, content: str, prompt: str):
        pass

    def update_prompt_chain_w_response(self, response: str, role: str = "assistant"):
        self.prompt_chain.append({"role": role, "content": response})

    def query(self, content: str, prompt: str):
        pass

    def query_msg_chain(self):
        pass

    @staticmethod
    def log(context: str, save_name: str):
        with open(save_name, "w") as f:
            f.write(context)


class Llama3(LLMBase):
    def __init__(self, model_name: str, temp: float = 0., top_p: float = 1.):
        super().__init__(temp, top_p)
        self.model_id = "meta-llama/Meta-{}".format(model_name)
        self.pipeline = pipeline(
            "text-generation",
            model=self.model_id,
            model_kwargs={
                "torch_dtype": torch.float16,
                "quantization_config": {
                    "load_in_4bit": True,
                    "bnb_4bit_compute_dtype": torch.bfloat16
                },
                "low_cpu_mem_usage": True,
            },
            device_map="auto"
        )
        self.terminators = [
            self.pipeline.tokenizer.eos_token_id,
            self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]

    def count_tokens(self, string: str):
        tokens = self.pipeline.tokenizer.tokenize(string)
        return len(tokens)

    def init_prompt_chain(self, content: str, prompt: str):
        assert len(self.prompt_chain) == 0, "Prompt chain is not empty!"
        self.prompt_chain.extend([{"role": "system", "content": content},
                                  {"role": "user", "content": prompt}])

    def update_prompt_chain(self, content: str, prompt: str):
        self.prompt_chain[0]["content"] = content
        self.prompt_chain.append({"role": "user", "content": prompt})

    def query(self, content: str, prompt: str):
        messages = [
            {"role": "system", "content": content},
            {"role": "user", "content": prompt}
        ]
        response = self.pipeline(
            messages,
            max_new_tokens=MAX_NEW_TOKENS,
            eos_token_id=self.terminators,
            pad_token_id=self.pipeline.tokenizer.eos_token_id,
            do_sample=True,
            # temperature=self.temperature,
            # top_p=self.top_p,
        )
        output = response[0]["generated_text"][-1]['content']
        torch.cuda.empty_cache()
        return output

    def query_msg_chain(self):
        response = self.pipeline(
            self.prompt_chain,
            max_new_tokens=MAX_NEW_TOKENS,
            eos_token_id=self.terminators,
            pad_token_id=self.pipeline.tokenizer.eos_token_id,
            do_sample=True,
            # temperature=self.temperature,
            # top_p=self.top_p,
        )
        output = response[0]["generated_text"][-1]['content']
        torch.cuda.empty_cache()
        return output


# ---------- Original DELTA: Azure OpenAI ----------
# The original DELTA uses Azure OpenAI API (AzureOpenAI client).
# Kept for reference but not used in HEART experiments.

class GPT(LLMBase):
    def __init__(self, model_name: str, temp: float = 0., top_p: float = 1.):
        super().__init__(temp, top_p)
        self.model_id = model_name
        self.key = os.getenv("AZURE_API_KEY")
        from openai import AzureOpenAI
        self.client = AzureOpenAI(
            api_key=self.key,
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_ENDPOINT")
        )

    def count_tokens(self, string: str):
        encoding_name = deepcopy(self.model_id)
        if "gpt-35" in encoding_name:
            encoding_name.replace("gpt-35", "gpt-3.5")
        encoding = tiktoken.encoding_for_model(encoding_name)
        return len(encoding.encode(string))

    def init_prompt_chain(self, content: str, prompt: str):
        assert len(self.prompt_chain) == 0, "Prompt chain is not empty!"
        self.prompt_chain.extend([{"role": "system", "content": content},
                                  {"role": "user", "content": prompt}])

    def update_prompt_chain(self, content: str, prompt: str):
        self.prompt_chain[0]["content"] = content
        self.prompt_chain.append({"role": "user", "content": prompt})

    def query(self, content: str, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model_id,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": content},
                {"role": "user", "content": prompt}
            ]
        )
        if getattr(response, "usage", None):
            self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content

    def query_msg_chain(self):
        response = self.client.chat.completions.create(
            model=self.model_id,
            temperature=self.temperature,
            messages=self.prompt_chain
        )
        if getattr(response, "usage", None):
            self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content


# ---------- HEART addition: OpenAI API (non-Azure) ----------
# Uses openai.OpenAI client instead of AzureOpenAI.
# This is the only class used in HEART experiments.

class OpenAIModel(LLMBase):
    def __init__(self, model_name: str, temp: float = 0., top_p: float = 1.):
        super().__init__(temp, top_p)
        self.model_id = model_name
        import openai
        self.key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.key
        self.client = openai.OpenAI()

    def count_tokens(self, string: str):
        encoding_name = deepcopy(self.model_id)
        if "gpt-35" in encoding_name:
            encoding_name.replace("gpt-35", "gpt-3.5")
        encoding = tiktoken.encoding_for_model(encoding_name)
        return len(encoding.encode(string))

    def init_prompt_chain(self, content: str, prompt: str):
        assert len(self.prompt_chain) == 0, "Prompt chain is not empty!"
        self.prompt_chain.extend([{"role": "system", "content": content},
                                  {"role": "user", "content": prompt}])

    def update_prompt_chain(self, content: str, prompt: str):
        self.prompt_chain[0]["content"] = content
        self.prompt_chain.append({"role": "user", "content": prompt})

    def query(self, content: str, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model_id,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": content},
                {"role": "user", "content": prompt}
            ]
        )
        if getattr(response, "usage", None):
            self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content

    def query_msg_chain(self):
        response = self.client.chat.completions.create(
            model=self.model_id,
            temperature=self.temperature,
            messages=self.prompt_chain
        )
        if getattr(response, "usage", None):
            self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content


# ---------- Factory function ----------

def load_llm(model_name: str, temp: float = 0., top_p: float = 1.):
    if "llama" in model_name.lower():
        return Llama3(model_name, temp, top_p)
    elif "gpt" in model_name.lower():
        # HEART: uses OpenAI API directly (not Azure)
        # Original DELTA: return GPT(model_name, temp, top_p)
        return OpenAIModel(model_name, temp, top_p)
    else:
        raise Exception("Invalid model name!")
