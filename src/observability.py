"""Rastreamento de execuções: Langfuse (instrumentação explícita) e LangSmith.

- Langfuse: ativo quando LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY estão definidas.
  O callback é passado na configuração de cada execução do workflow.
- LangSmith: o LangChain/LangGraph o ativa sozinho com LANGSMITH_TRACING=true e
  LANGSMITH_API_KEY. Nada precisa ser passado no código.

Os rastros podem conter a receita e o aviso de saúde. Eles saem do processo
para o serviço escolhido, então use chaves de um projeto próprio.
"""

import os
from typing import Any

from dotenv import load_dotenv


def langfuse_enabled() -> bool:
    load_dotenv()
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
        and os.getenv("LANGFUSE_SECRET_KEY", "").strip()
    )


def langfuse_callbacks() -> list[Any]:
    """Devolve o callback do Langfuse, ou lista vazia se não houver chaves."""
    if not langfuse_enabled():
        return []

    from langfuse.langchain import CallbackHandler

    return [CallbackHandler()]
