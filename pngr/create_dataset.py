"""Create a dataset of polar prompts."""

from typing import Any, Dict, List

import yaml

from .vector_readers import DatasetEntry


def load_yaml_template(file_path: str) -> List[Dict[str, Any]]:
    """Load YAML template file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_personality_prompts(
    template_path: str = "dataset_templates/alphapenger.yaml",
    a_adjective: str = "good-hearted",
    b_adjective: str = "mischievous",
) -> List[DatasetEntry]:
    """Create prompts interpolated with two different personalities."""

    templates = load_yaml_template(template_path)
    prompts = []

    for template in templates:
        # Get system template and user prompts
        system_template = template["system_template"]
        user_prompts = template["prompts"]

        # Create prompts for first personality
        system1 = system_template.format(identity=a_adjective)
        system2 = system_template.format(identity=b_adjective)

        for user_prompt in user_prompts:
            prompts.append(
                {
                    "a": [
                        {"role": "system", "content": system1},
                        {"role": "user", "content": user_prompt},
                    ],
                    "b": [
                        {"role": "system", "content": system2},
                        {"role": "user", "content": user_prompt},
                    ],
                }
            )

    return prompts


def save_prompts(
    prompts: List[Dict[str, str]], output_file: str = "vector_dataset.jsonl"
):
    """Save prompts to JSONL file."""
    import json

    with open(output_file, "w", encoding="utf-8") as f:
        for prompt in prompts:
            f.write(json.dumps(prompt) + "\n")
