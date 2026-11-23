"""Servidor da API para o teste de queda: agentes falsos, banco em SQLite.

Uso (o teste chama assim): python -m tests.crash_server --port 8123
O banco e a pasta de imagens vêm de DATABASE_PATH, CHECKPOINT_DATABASE_PATH e
IMAGE_STORAGE_DIR, definidos pelo teste em um diretório temporário.
"""

import argparse

import uvicorn

from src.graph import builder as graph_module
from tests.fakes import install_offline_agents


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    # Antes de montar a sessão: o grafo lê os nós no momento da construção.
    install_offline_agents(graph_module)

    from src.api.app import create_app

    uvicorn.run(create_app(), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
