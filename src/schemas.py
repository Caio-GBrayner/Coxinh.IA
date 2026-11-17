from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class Recipe(BaseModel):
    dough: NonEmptyText = Field(description="Description of the coxinha dough.")
    filling: NonEmptyText = Field(description="Description of the filling.")
    ingredients: list[NonEmptyText] = Field(
        min_length=1,
        description="Every ingredient used in the dough, filling, and preparation.",
    )
    preparation: NonEmptyText = Field(
        description="Preparation instructions for the proposed recipe."
    )
    utensils: list[NonEmptyText] = Field(
        description="Every utensil needed to prepare the recipe."
    )
    preparation_methods: list[NonEmptyText] = Field(
        description="Every cooking method used by the recipe."
    )
    revision_summary: NonEmptyText | None = Field(
        default=None,
        description="Summary of changes from the previous proposal, if any.",
    )


class SubChefEvaluation(BaseModel):
    decision: Literal["approved", "rejected"]
    critique: str
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rejection_critique(self) -> Self:
        if self.decision == "rejected" and not self.critique.strip():
            raise ValueError("A rejected proposal must include a critique.")

        return self
