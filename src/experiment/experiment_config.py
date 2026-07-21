from __future__ import annotations

from dataclasses import dataclass, field

from src.config import DEFAULT_MODEL_ID, GenerationConfig, ModelLoadConfig


@dataclass(frozen=True)
class TeachingStrategyExperimentConfig:
    """Configuration for the core teaching strategy experiment."""

    class_id: str = "class_3_basic"
    teacher_id: str = "T001"
    curriculum_path: str = "data/curriculum/linear_equation.json"
    classes_dir: str = "data/classes"
    students_dir: str = "data/students"
    logs_dir: str = "data/logs"
    teacher_beliefs_dir: str = "data/teacher_beliefs"
    total_minutes: int = 30
    use_mock_student: bool = True
    update_student_knowledge: bool = False
    model_id: str = DEFAULT_MODEL_ID
    generation_config: GenerationConfig = field(default_factory=GenerationConfig)
    model_load_config: ModelLoadConfig = field(default_factory=ModelLoadConfig)
