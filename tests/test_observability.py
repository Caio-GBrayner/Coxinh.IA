import pytest

from src import observability


def test_langfuse_is_off_without_keys(monkeypatch):
    """Sem as duas chaves, nenhum callback é criado e nada sai do processo."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")

    assert observability.langfuse_enabled() is False
    assert observability.langfuse_callbacks() == []


def test_langfuse_needs_both_keys(monkeypatch):
    """Uma chave sozinha não ativa o Langfuse."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")

    assert observability.langfuse_enabled() is False


def test_langfuse_callback_is_created_when_keys_exist(monkeypatch):
    """Com as duas chaves, o workflow recebe o callback do Langfuse.

    O callback real é substituído: o teste não pode exportar spans para fora.
    """
    pytest.importorskip("langfuse.langchain")
    import langfuse.langchain as langfuse_langchain

    created = []

    class FakeHandler:
        def __init__(self) -> None:
            created.append(self)

    monkeypatch.setattr(langfuse_langchain, "CallbackHandler", FakeHandler)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    callbacks = observability.langfuse_callbacks()

    assert len(callbacks) == 1
    assert isinstance(callbacks[0], FakeHandler)
