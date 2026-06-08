"""Testes automatizados da API do Cronograma de Estudos."""
import pytest
from httpx import ASGITransport, AsyncClient
from main import app, Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    """Cria um banco temporário antes de cada teste."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

