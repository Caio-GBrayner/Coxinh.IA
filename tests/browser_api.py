"""API real para testes de navegador; só os agentes externos são substituídos.

Não usar em produção. Executar pelo Playwright, sem credenciais nem chamadas pagas.
"""
import os

from src.graph import builder
from src.schemas import CookOutput, Recipe, SubChefEvaluation


os.environ["GUARD_ENABLED"] = "false"


def chef(state):
    return {
        "recipe": Recipe(
            dough="Massa de batata", filling="Frango",
            ingredients=["batata", "frango", *state.get("ingredient_additions", [])],
            preparation="Cozinhe e modele.", utensils=["panela"],
            preparation_methods=["cozimento"],
        ),
        "recipe_version": state["recipe_version"] + 1,
    }


def subchef(state):
    paused = "impasse" in state["raw_input"].lower() and not state.get("user_guidance")
    return {"subchef_evaluation": SubChefEvaluation(
        decision="rejected" if paused else "approved",
        critique="Explique como deseja ajustar o preparo." if paused else "",
    )}


def cook(state):
    recipe = state["recipe"]
    return {
        "cook_output": CookOutput(
            title="Coxinha de teste da cozinha", subtitle="Massa de batata e frango.",
            steps=["Cozinhe as batatas.", "Modele e recheie a coxinha."],
            image_prompt="Uma coxinha aberta.", ingredients=recipe.ingredients,
            utensils=recipe.utensils, preparation_methods=recipe.preparation_methods,
        ),
        "cook_resource_validation": "valid",
    }


builder.chef_node = chef
builder.subchef_node = subchef
builder.cook_node = cook
builder.health_node = lambda _: {
    "health_warning": "Aviso de teste, sem avaliação real de consumo.",
    "health_status": "insufficient", "health_sources": [],
    "health_uncertainty": "Fontes externas simuladas neste teste.",
}
builder.image_node = lambda _: {"image_status": "generated", "image_url": "simulated://browser-test"}

from src.api.app import create_app  # noqa: E402

from src.recipe_session import RecipeSession

app = create_app(RecipeSession())
