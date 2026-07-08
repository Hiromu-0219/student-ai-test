from __future__ import annotations

from src.config import DEFAULT_MODEL_ID, GenerationConfig


class LocalLLM:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        *,
        load_in_4bit: bool = True,
        generation_config: GenerationConfig | None = None,
    ) -> None:
        self.model_id = model_id
        self.load_in_4bit = load_in_4bit
        self.generation_config = generation_config or GenerationConfig()
        self.tokenizer = None
        self.model = None

    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        quantization_config = None
        if self.load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            device_map="auto",
            quantization_config=quantization_config,
            torch_dtype=torch.bfloat16 if not self.load_in_4bit else None,
            trust_remote_code=True,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.model is None or self.tokenizer is None:
            self.load()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            try:
                prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
            except TypeError:
                prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
        else:
            prompt = f"{system_prompt}\n\n{user_prompt}\n\n回答:"

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.generation_config.max_new_tokens,
            do_sample=True,
            temperature=self.generation_config.temperature,
            top_p=self.generation_config.top_p,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        generated = outputs[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()
