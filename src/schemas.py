from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator


TextoObrigatorio = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class Receita(BaseModel):
    massa: TextoObrigatorio
    recheio: TextoObrigatorio
    ingredientes: list[TextoObrigatorio] = Field(min_length=1)
    modo_de_preparo: TextoObrigatorio
    resumo_da_revisao: TextoObrigatorio | None = None

class AvaliacaoSubchef(BaseModel):
    decision: Literal["approved", "rejected"]
    critique: str
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_critica(self) -> Self:
        if self.decision == "rejected" and not self.critique.strip():
            raise ValueError(
                "Uma proposta rejeitada precisa de uma crítica."
            )

        return self