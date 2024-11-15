"""
Command-line interface for cli.
"""

from pathlib import Path
from typing import Optional
import click
from IPython import start_ipython
from rich.console import Console
from rich.traceback import install as rich_traceback_install
from palinor.manager import palinorManager
from palinor.create_dataset import create_personality_prompts, save_prompts
from palinor import create_dataset

rich_traceback_install()
console = Console()


class palinorShell:
    """Interactive shell helper for palinor operations."""

    def __init__(self, manager: palinorManager):
        self.manager = manager
        self.datasets = {}  # Store created datasets

    def create_dataset(
        self, name: str, a_trait: str, b_trait: str, template_path: Optional[str] = None
    ):
        """Create a new dataset of personality prompts."""
        if template_path is None:
            template_path = str(
                Path(__file__).parent.parent / "dataset_templates/alphapenger.yaml"
            )

        prompts = create_dataset.create_personality_prompts(
            template_path, a_trait, b_trait
        )

        # Save to ~/.palinor/datasets/
        datasets_dir = Path.home() / ".palinor" / "datasets"
        datasets_dir.mkdir(parents=True, exist_ok=True)
        output_path = datasets_dir / f"{name}.jsonl"

        create_dataset.save_prompts(prompts, str(output_path))
        self.datasets[name] = prompts
        console.print(
            f"[green]Created dataset '{name}' with {len(prompts)} prompts[/green]"
        )
        console.print(f"[green]Saved to {output_path}[/green]")

    def list_datasets(self):
        """List all available datasets."""
        if not self.datasets:
            console.print("[yellow]No datasets created yet[/yellow]")
            return

        console.print("[bold]Available datasets:[/bold]")
        for name, dataset in self.datasets.items():
            console.print(f"  • {name} ({len(dataset)} prompts)")

    def train_vector(self, name: str, dataset_name: str):
        """Train a new control vector using a dataset."""
        if dataset_name not in self.datasets:
            console.print(f"[red]Dataset '{dataset_name}' not found[/red]")
            return

        dataset = self.datasets[dataset_name]
        with console.status(f"Training vector '{name}'..."):
            self.manager.train_vector(name, dataset[0].a_trait, dataset[0].b_trait)
        console.print(f"[green]Vector {name} trained and saved![/green]")

    def list_vectors(self):
        """List all available vectors."""
        vectors = self.manager.list_vectors()
        if not vectors:
            console.print("[yellow]No vectors available[/yellow]")
            return

        console.print("[bold]Available vectors:[/bold]")
        for vector in vectors:
            console.print(f"  • {vector}")

    def complete(
        self, prompt: str, vector: Optional[str] = None, strength: float = 1.0
    ):
        """Complete text with optional vector control."""
        output = self.manager.generate(prompt, vector_name=vector, coeff=strength)
        console.print("\n[bold]Generated text:[/bold]")
        console.print(output)
        return output

    def help(self):
        """Show available commands."""
        console.print("[bold]Available commands:[/bold]")
        console.print(" • shell.[green]create_dataset[/green](name, a_trait, b_trait)")
        console.print(" • shell.[green]list_datasets[/green]()")
        console.print(" • shell.[green]train_vector[/green](name, dataset_name)")
        console.print(" • shell.[green]list_vectors[/green]()")
        console.print(
            " • shell.[green]complete[/green](prompt, vector=None, strength=1.0)"
        )
        console.print(" • shell.[green]help[/green]()")


@click.group()
def cli():
    """palinor CLI for controlling language models."""
    pass


@click.command()
@click.argument("name")
@click.argument("a_trait")
@click.argument("b_trait")
@click.option("--templates", "-t", type=click.Path(exists=True))
def dataset(name: str, a_trait: str, b_trait: str, templates: Optional[str]) -> None:
    """Create a dataset of personality prompts."""
    # Create datasets directory
    datasets_dir = Path.home() / ".palinor" / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)

    template_path = (
        templates or Path(__file__).parent.parent / "dataset_templates/alphapenger.yaml"
    )
    prompts = create_personality_prompts(str(template_path), a_trait, b_trait)

    # Save to ~/.palinor/datasets/
    output_path = datasets_dir / f"{name}.jsonl"
    save_prompts(prompts, str(output_path))
    console.print(f"[green]Dataset saved to {output_path}[/green]")


@click.command()
@click.argument("name")
@click.argument("a_trait")
@click.argument("b_trait")
@click.option(
    "--model", "-m", help="Model to use", default="meta-llama/Llama-3.2-1B-Instruct"
)
@click.option("--token", help="HuggingFace token for gated models")
def train(name: str, a_trait: str, b_trait: str, model: str, token: Optional[str]):
    """Train a new control vector."""
    manager = palinorManager(model, hf_token=token)
    with console.status(f"Training vector '{name}' ({a_trait} vs {b_trait})..."):
        manager.train_vector(name, a_trait, b_trait)
    console.print(f"[green]Vector {name} trained and saved![/green]")


@click.command()
@click.argument("prompt")
@click.option(
    "--model", "-m", help="Model to use", default="meta-llama/Llama-3.2-1B-Instruct"
)
@click.option("--vector", "-v", help="Vector to use")
@click.option("--strength", "-s", help="Control strength", default=1.0, type=float)
@click.option("--token", help="HuggingFace token for gated models")
def complete(
    prompt: str,
    model: str,
    vector: Optional[str],
    strength: float,
    token: Optional[str],
):
    """Generate text with optional vector control."""
    manager = palinorManager(model, hf_token=token)
    output = manager.generate(prompt, vector_name=vector, coeff=strength)
    console.print("\n[bold]Generated text:[/bold]")
    console.print(output)


@click.command()
@click.option(
    "--model", "-m", help="Model to use", default="meta-llama/Llama-3.2-1B-Instruct"
)
def list_vectors(model: str):
    """List available vectors for a model."""
    manager = palinorManager(model)
    vectors = manager.list_vectors()
    if vectors:
        console.print("[bold]Available vectors:[/bold]")
        for vector in vectors:
            console.print(f"  • {vector}")
    else:
        console.print("[yellow]No vectors found for this model[/yellow]")


@click.command()
@click.option(
    "--model", "-m", help="Model to use", default="meta-llama/Llama-3.2-1B-Instruct"
)
def shell(model: str):
    """Start a shell after initialising a manager."""
    manager = palinorManager(model_name=model)
    shell_helper = palinorShell(manager)

    banner = (
        f"palinor shell for model {model}\n" "Type shell.help() for available commands"
    )
    start_ipython(
        argv=[], user_ns={"manager": manager, "shell": shell_helper}, banner1=banner
    )


# Add commands to CLI group
cli.add_command(dataset)
cli.add_command(train)
cli.add_command(complete)
cli.add_command(list_vectors)
cli.add_command(shell)

if __name__ == "__main__":
    cli()
