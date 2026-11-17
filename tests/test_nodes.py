import json
from unittest.mock import Mock

from langchain_core.messages import HumanMessage
import pytest

from src.nodes import chef, subchef
from src.schemas import Recipe, SubChefEvaluation
from src.state import create_initial_state


def create_recipe():
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def test_chef_returns_structured_recipe_and_increments_recipe_version(monkeypatch):
    state = create_initial_state(
        "Quero uma coxinha de batata e frango.",
        "conversation-1",
    )
    state["authorized_ingredients"] = ["potato", "chicken"]
    state["user_preferences"] = {"tone": "playful"}

    structured_model = Mock()
    structured_model.invoke.return_value = create_recipe()
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_model
    mocked_call_llm = Mock(return_value=chat_model)
    monkeypatch.setattr(chef, "call_llm", mocked_call_llm)

    result = chef.chef_node(state)

    mocked_call_llm.assert_called_once_with(chef.CHEF_TEMPERATURE)
    chat_model.with_structured_output.assert_called_once_with(Recipe)
    assert result == {
        "recipe": create_recipe(),
        "recipe_version": 1,
    }

    messages = structured_model.invoke.call_args.args[0]
    context = json.loads(messages[1].content)
    assert isinstance(messages[1], HumanMessage)
    assert context["request"] == state["raw_input"]
    assert context["authorized_ingredients"] == ["potato", "chicken"]
    assert context["user_preferences"] == {"tone": "playful"}


def test_chef_includes_previous_recipe_and_rejection_critique(monkeypatch):
    state = create_initial_state("Make a coxinha.", "conversation-1")
    state["recipe"] = create_recipe()
    state["subchef_evaluation"] = SubChefEvaluation(
        decision="rejected",
        critique="Include a clearer preparation method.",
    )

    structured_model = Mock()
    structured_model.invoke.return_value = create_recipe()
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_model
    monkeypatch.setattr(chef, "call_llm", Mock(return_value=chat_model))

    chef.chef_node(state)

    context = json.loads(structured_model.invoke.call_args.args[0][1].content)
    assert context["previous_recipe"]["filling"] == "Chicken"
    assert context["previous_critique"] == "Include a clearer preparation method."
    assert context["next_recipe_version"] == 1


def test_subchef_rejects_resource_violations_without_llm_call(monkeypatch):
    state = create_initial_state("Make a coxinha.", "conversation-1")
    state["recipe"] = create_recipe()
    state["authorized_ingredients"] = ["potato"]
    state["authorized_utensils"] = ["pot"]
    state["authorized_preparation_methods"] = ["boiling"]
    mocked_call_llm = Mock()
    monkeypatch.setattr(subchef, "call_llm", mocked_call_llm)

    result = subchef.subchef_node(state)

    evaluation = result["subchef_evaluation"]
    assert evaluation.decision == "rejected"
    assert "chicken" in evaluation.evidence[0]
    mocked_call_llm.assert_not_called()


def test_subchef_uses_structured_output_without_original_request(monkeypatch):
    state = create_initial_state(
        "Original user request should not be reviewer context.",
        "conversation-1",
    )
    state["recipe"] = create_recipe()
    state["authorized_ingredients"] = ["potato", "chicken"]
    state["authorized_utensils"] = ["pot"]
    state["authorized_preparation_methods"] = ["boiling"]

    expected_evaluation = SubChefEvaluation(
        decision="approved",
        critique="",
        evidence=["The structured recipe is coherent."],
    )
    structured_model = Mock()
    structured_model.invoke.return_value = expected_evaluation
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_model
    mocked_call_llm = Mock(return_value=chat_model)
    monkeypatch.setattr(subchef, "call_llm", mocked_call_llm)

    result = subchef.subchef_node(state)

    mocked_call_llm.assert_called_once_with(subchef.SUBCHEF_TEMPERATURE)
    chat_model.with_structured_output.assert_called_once_with(SubChefEvaluation)
    assert result == {"subchef_evaluation": expected_evaluation}

    messages = structured_model.invoke.call_args.args[0]
    assert "Original user request" not in messages[1].content
    context = json.loads(messages[1].content)
    assert context["resource_validation"]["status"] == "passed"


def test_subchef_marks_unconfigured_resource_categories_as_unverified(monkeypatch):
    state = create_initial_state("Make a coxinha.", "conversation-1")
    state["recipe"] = create_recipe()

    structured_model = Mock()
    structured_model.invoke.return_value = SubChefEvaluation(
        decision="approved",
        critique="",
    )
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_model
    monkeypatch.setattr(subchef, "call_llm", Mock(return_value=chat_model))

    result = subchef.subchef_node(state)
    evidence = result["subchef_evaluation"].evidence

    assert any("ingredients was not provided" in item for item in evidence)


def test_subchef_requires_a_recipe():
    state = create_initial_state("Make a coxinha.", "conversation-1")

    with pytest.raises(
        ValueError,
        match="The SubChef requires a recipe to review",
    ):
        subchef.subchef_node(state)
