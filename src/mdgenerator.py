from jinja2 import Environment, FileSystemLoader

from src.models import CivitaiModel


def model_to_markdown(model: CivitaiModel) -> str:
    env = Environment(loader=FileSystemLoader("src/templates"))
    template = env.get_template("model.md.j2")
    return template.render(model=model)


def models_to_markdown(models: list[CivitaiModel]) -> str:
    env = Environment(loader=FileSystemLoader("src/templates"))
    template = env.get_template("index.md.j2")
    return template.render(models=models)
