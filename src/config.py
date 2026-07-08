from __future__ import annotations

from dataclasses import dataclass


DEFAULT_MODEL_ID = "Qwen/Qwen3-4B"
DEFAULT_STUDENTS_DIR = "data/students"
DEFAULT_LOGS_DIR = "data/logs"


@dataclass(frozen=True)
class GenerationConfig:
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    do_sample: bool = True
    repetition_penalty: float = 1.05


@dataclass(frozen=True)
class ModelLoadConfig:
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    compute_dtype: str = "bfloat16"
