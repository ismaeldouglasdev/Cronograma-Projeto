"""Testes automatizados da API do Cronograma de Estudos.

Cobre: auth, areas, tasks, sessoes, gamificacao, coins, rate limit.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import date
from httpx import ASGITransport, AsyncClient
from main import app
from config import Base, engine
from middleware import rate_limiter
import routes.gamification as gamification_module


@pytest.fixture(autouse=True)
def setup_db():
    """Recria banco isolado para cada teste."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limiter._store.clear()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP assíncrono por teste."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    """Registra e loga um usuário, retorna headers com token."""
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "Test1234!@"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Auth Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_creates_user(client):
    r = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "Test1234!@"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "Test1234!@"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    r = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "Test1234!@"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_weak_password(client):
    r = await client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "Test1234!@"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "wp@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "wp@example.com", "password": "WrongPass1!"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_required_for_areas(client):
    r = await client.get("/areas")
    assert r.status_code == 401


# ─── Areas Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_area(client, auth_headers):
    r = await client.post(
        "/areas",
        json={"nome": "Matemática", "cor": "#ff0000"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Matemática"


@pytest.mark.asyncio
async def test_create_area_xss_escaped(client, auth_headers):
    """XSS no nome deve ser escapado."""
    r = await client.post(
        "/areas",
        json={"nome": "<script>alert(1)</script>", "cor": "#000"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert "<script>" not in r.json()["nome"]
    assert "&lt;script&gt;" in r.json()["nome"]


@pytest.mark.asyncio
async def test_list_areas_only_own(client, auth_headers):
    await client.post(
        "/areas", json={"nome": "A1"}, headers=auth_headers
    )
    # Outro user
    await client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "Test1234!@"},
    )
    r2 = await client.post(
        "/auth/login",
        json={"email": "other@example.com", "password": "Test1234!@"},
    )
    other_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    r = await client.get("/areas", headers=other_headers)
    assert r.status_code == 200
    assert len(r.json()) == 0


@pytest.mark.asyncio
async def test_update_area(client, auth_headers):
    r = await client.post(
        "/areas", json={"nome": "Original"}, headers=auth_headers
    )
    area_id = r.json()["id"]
    r2 = await client.patch(
        f"/areas/{area_id}",
        json={"nome": "Atualizada"},
        headers=auth_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Atualizada"


@pytest.mark.asyncio
async def test_delete_area_cascades_tasks_sessions(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "X"}, headers=auth_headers)
    ).json()
    task = (
        await client.post(
            "/tasks",
            json={
                "area_id": area["id"],
                "titulo": "T1",
                "data_entrega": str(date.today()),
            },
            headers=auth_headers,
        )
    ).json()
    await client.post(
        "/sessoes",
        json={"area_id": area["id"], "duracao_minutos": 30},
        headers=auth_headers,
    )
    r = await client.delete(f"/areas/{area['id']}", headers=auth_headers)
    assert r.status_code == 204
    # Task foi deletada
    r2 = await client.get("/tasks", headers=auth_headers)
    assert all(t["id"] != task["id"] for t in r2.json())


# ─── Tasks Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task_with_invalid_area(client, auth_headers):
    r = await client.post(
        "/tasks",
        json={
            "area_id": 9999,
            "titulo": "T1",
            "data_entrega": str(date.today()),
        },
        headers=auth_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_complete_task_awards_xp(client, auth_headers):
    r = await client.post(
        "/tasks",
        json={
            "titulo": "Tarefa XP",
            "data_entrega": str(date.today()),
        },
        headers=auth_headers,
    )
    task_id = r.json()["id"]
    await client.patch(
        f"/tasks/{task_id}",
        json={"concluida": True},
        headers=auth_headers,
    )
    r2 = await client.get("/gamification-summary", headers=auth_headers)
    assert r2.json()["xp_total"] >= 5


# ─── Sessoes Tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_sessao_updates_streak(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "A"}, headers=auth_headers)
    ).json()
    await client.post(
        "/sessoes",
        json={"area_id": area["id"], "duracao_minutos": 25},
        headers=auth_headers,
    )
    r = await client.get("/gamification-summary", headers=auth_headers)
    assert r.json()["current_streak"] >= 1


@pytest.mark.asyncio
async def test_pomodoro_awards_coins(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "A"}, headers=auth_headers)
    ).json()
    r = await client.post(
        "/pomodoro/completar",
        json={"area_id": area["id"], "duracao_minutos": 25},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["coins"] == 3


# ─── Gamification Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_freeze_requires_coins(client, auth_headers):
    r = await client.post("/coins/buy-freeze", headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_buy_freeze_success(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "A"}, headers=auth_headers)
    ).json()
    # 4 pomodoros = 12 coins
    for _ in range(4):
        await client.post(
            "/pomodoro/completar",
            json={"area_id": area["id"], "duracao_minutos": 25},
            headers=auth_headers,
        )
    r = await client.post("/coins/buy-freeze", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["coins"] == 2
    assert r.json()["freezes"] == 1


@pytest.mark.asyncio
async def test_add_coins_rejects_negative(client, auth_headers, monkeypatch):
    monkeypatch.setattr(gamification_module, "MIGRATION_SECRET", "test-secret")
    r = await client.post("/coins/add?amount=-5&secret=test-secret", headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_add_coins_rejects_over_100(client, auth_headers, monkeypatch):
    monkeypatch.setattr(gamification_module, "MIGRATION_SECRET", "test-secret")
    r = await client.post("/coins/add?amount=101&secret=test-secret", headers=auth_headers)
    assert r.status_code == 400


# ─── Resumo Tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resumo_horas_por_area(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "X"}, headers=auth_headers)
    ).json()
    await client.post(
        "/sessoes",
        json={"area_id": area["id"], "duracao_minutos": 60},
        headers=auth_headers,
    )
    r = await client.get("/sessoes/resumo", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["total_horas"] == 1.0

# ─── Regressão: registro (2026-09-27) ─────────────────────────────────────────
#
# Bug reportado: não dava para criar conta. O POST /auth/register devolvia 400
# e logo em seguida 429. Causas: (1) o backend exigia caractere especial na
# senha sem o formulário fazer a menor ideia; (2) o rate limit ficava no topo
# do handler, então cada 400 gastava uma das 5 vagas e o usuário era travado
# a seguir; (3) o limiter usava a entrada mais à esquerda do X-Forwarded-For,
# que é controlada pelo cliente e permitia burlar o limite por completo.

VALID_SENHA_SEM_ESPECIAL = "ismael2006"


@pytest.mark.asyncio
async def test_register_aceita_senha_sem_caractere_especial(client):
    """Regra (b): 8+ chars, uma letra e um número chegam. Especial é opcional."""
    r = await client.post(
        "/auth/register",
        json={"email": "sem-especial@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
    )
    assert r.status_code == 200, r.text
    assert "access_token" in r.json()

    login = await client.post(
        "/auth/login",
        json={"email": "sem-especial@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
    )
    assert login.status_code == 200, "a senha aceita no registro tem que entrar no login"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "senha",
    ["curta1a", "senhasemnumero", "1234567890"],
    ids=["curta", "sem_numero", "sem_letra"],
)
async def test_register_ainda_rejeita_senha_fraca(client, senha):
    """As três regras que sobraram continuam valendo."""
    r = await client.post(
        "/auth/register",
        json={"email": f"fraca-{len(senha)}@example.com", "password": senha},
    )
    assert r.status_code == 400
    assert r.json()["detail"]


@pytest.mark.asyncio
async def test_erro_de_validacao_nao_queima_a_cota_do_rate_limit(client):
    """Regressão do 400 -> 429: erros de validação não devem contar como tentativa.

    Antes, o limiter rodava antes de validar, então 5 senhas frágeis travavam
    o cadastro por 60s mesmo sem nenhuma consulta ao banco.
    """
    for _ in range(12):
        r = await client.post(
            "/auth/register",
            json={"email": "curto@example.com", "password": "abc"},
        )
        assert r.status_code == 400, f"esperava 400, veio {r.status_code}: {r.text}"

    # ...e logo depois um cadastro válido tem que passar.
    ok = await client.post(
        "/auth/register",
        json={"email": "depois-dos-400@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
    )
    assert ok.status_code == 200, ok.text


@pytest.mark.asyncio
async def test_429_traz_retry_after_e_tempo_acionavel(client):
    """O 429 precisa dizer quanto tempo esperar, não só 'tente de novo'."""
    respostas = []
    for i in range(25):
        r = await client.post(
            "/auth/register",
            json={"email": f"enum-{i}@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
        )
        respostas.append(r)
        if r.status_code == 429:
            break

    bloqueou = next((r for r in respostas if r.status_code == 429), None)
    assert bloqueou is not None, "esperava estourar o limite de enumeração"

    retry_after = int(bloqueou.headers["Retry-After"])
    assert 1 <= retry_after <= 60
    assert f"{retry_after}s" in bloqueou.json()["detail"]


@pytest.mark.asyncio
async def test_rate_limit_nao_pode_ser_burlado_com_x_forwarded_for(client):
    """Regressão de segurança: o limiter não pode usar IP controlável pelo cliente.

    O uvicorn escreve a entrada mais à ESQUERDA do X-Forwarded-For em
    request.client.host, e essa entrada é o que o cliente mandar. Antes
        X-Forwarded-For: 10.0.0.<varying>
    dava 200 em todo request, estourando o limite de 5/min sem esforço.
    """
    status_codes = []
    for i in range(12):
        r = await client.post(
            "/auth/register",
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
            json={"email": f"spoof-{i}@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
        )
        status_codes.append(r.status_code)
        if r.status_code == 429:
            break

    assert 429 in status_codes, f"limite nunca estourou: {status_codes}"
    assert len(status_codes) <= 12


@pytest.mark.asyncio
async def test_cf_connecting_ip_tem_precedencia(client):
    """Cloudflare está na frente e substitui esse header pelo IP real do visitante."""
    status_codes = []
    for i in range(12):
        r = await client.post(
            "/auth/register",
            headers={"CF-Connecting-IP": "203.0.113.7"},
            json={"email": f"cf-{i}@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
        )
        status_codes.append(r.status_code)
        if r.status_code == 429:
            break

    assert 429 in status_codes, f"limite nunca estourou: {status_codes}"


@pytest.mark.asyncio
async def test_email_ja_cadastrado_diz_para_entrar(client):
    """O 400 de duplicado precisa orientar o usuário, não só poupar."""
    await client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
    )
    r = await client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
    )
    assert r.status_code == 400
    assert "login" in r.json()["detail"].lower()


class _FakeClient:
    def __init__(self, host):
        self.host = host


class _FakeRequest:
    """Request mínimo para exercitar get_client_ip sem subir o servidor."""

    def __init__(self, headers=None, host="189.40.10.5"):
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.client = _FakeClient(host)


@pytest.mark.asyncio
async def test_get_client_ip_ignora_x_forwarded_for():
    """X-Forwarded-For é controlado por quem faz o request — não pode virar chave.

    Se o limiter confiasse nele, bastava trocar o valor a cada chamada para
    nunca estourar o limite. Foi assim que 8 requests passaram com limite
    de 5/min em produção.
    """
    from middleware import get_client_ip

    req = _FakeRequest(headers={"X-Forwarded-For": "9.9.9.9"})
    assert get_client_ip(req) == "189.40.10.5", "caiu no XFF falsificado"


@pytest.mark.asyncio
async def test_get_client_ip_preferindo_cloudflare():
    """CF-Connecting-IP é substituído pela Cloudflare pelo IP real do visitante."""
    from middleware import get_client_ip

    req = _FakeRequest(headers={"CF-Connecting-IP": "189.40.20.7", "X-Forwarded-For": "9.9.9.9"})
    assert get_client_ip(req) == "189.40.20.7"


@pytest.mark.asyncio
async def test_get_client_ip_ignora_cf_connecting_ip_privado():
    """Header que resolve para rede privada não serve de identidade."""
    from middleware import get_client_ip

    req = _FakeRequest(headers={"CF-Connecting-IP": "10.0.0.5"})
    assert get_client_ip(req) == "189.40.10.5"


@pytest.mark.asyncio
async def test_xff_nao_burla_o_limite_de_registro(client):
    """Regressão de ponta a ponta: varies o XFF e o limite ainda segura."""
    status_codes = []
    for i in range(12):
        r = await client.post(
            "/auth/register",
            headers={"X-Forwarded-For": f"189.40.30.{i}"},
            json={"email": f"uvicorn-spoof-{i}@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
        )
        status_codes.append(r.status_code)
        if r.status_code == 429:
            break

    assert 429 in status_codes, f"o XFF ainda controla a chave do limiter: {status_codes}"


@pytest.mark.asyncio
async def test_limite_geral_responde_429_e_nao_500(client):
    """Regressão: o 429 do limiter geral virava 500.

    log_requests_middleware devolvia Response(content={"detail": ...}), mas o
    Starlette exige str/bytes em content — estourar 120 req/min derrubava a
    resposta com 500 em vez de dizer 'tente de novo'.
    """
    status_codes = []
    for _ in range(130):
        r = await client.get("/auth/check")
        status_codes.append(r.status_code)
        if r.status_code == 429:
            break

    assert 429 in status_codes, f"limite geral nunca disparou: {status_codes[:5]}"
    assert 500 not in status_codes, "o 429 do limiter geral virou 500"
    assert r.headers.get("Retry-After"), "o 429 do limiter geral precisa de Retry-After"


def test_regras_de_senha_js_e_python_batem():
    """As duas listas de regras precisam continuar idênticas.

    O bug de 2026-09-27 nasceu da divergência: o backend exigia caractere
    especial e o frontend não tinha regra nenhuma, então a UI aceitava senhas
    que a API rejeitava com 400. Este teste falha no primeiroSignal de divergência.
    """
    import re as _re
    from pathlib import Path

    from middleware import PASSWORD_MIN_LENGTH, PASSWORD_RULES

    js_path = Path(__file__).parent / "static" / "auth.js"
    js = js_path.read_text(encoding="utf-8")

    bloco = _re.search(r"const PASSWORD_RULES = \[(.*?)\n  \];", js, _re.S)
    assert bloco, "não achei PASSWORD_RULES em static/auth.js — renomeou?"

    js_length = _re.search(r"v\.length >= (\d+)", bloco.group(1))
    assert js_length, "regra de tamanho não encontrada no JS"
    assert int(js_length.group(1)) == PASSWORD_MIN_LENGTH, (
        f"JS exige {js_length.group(1)} caracteres, Python exige {PASSWORD_MIN_LENGTH}"
    )

    js_tests = _re.findall(r"test: \(v\) => /(.+?)/\.test\(v\)", bloco.group(1))
    py_tests = [pattern for pattern, _ in PASSWORD_RULES]

    # A regra de comprimento é expressa diferente nos dois lados (.length vs regex).
    js_sem_tamanho = [t for t in js_tests if "{8,}" not in t]
    py_sem_tamanho = [p for p in py_tests if "{%d,}" % PASSWORD_MIN_LENGTH not in p]

    assert len(js_sem_tamanho) == len(py_sem_tamanho), (
        f"quantidade de regras divergiu: JS {len(js_sem_tamanho)}, Python {len(py_sem_tamanho)}"
    )
    assert js_sem_tamanho == py_sem_tamanho, (
        f"regras divergiram.\n  JS:     {js_sem_tamanho}\n  Python: {py_sem_tamanho}"
    )

    # A regra de caractere especial não pode voltar só de um lado.
    assert "caractere especial" not in js
    assert not any("special" in m for _, m in PASSWORD_RULES)


@pytest.mark.asyncio
async def test_429_no_front_usa_retry_after(client):
    """O 429 precisa ser traduzível: mensagem dinâmica com o número de segundos."""
    for i in range(25):
        r = await client.post(
            "/auth/register",
            json={"email": f"front-{i}@example.com", "password": VALID_SENHA_SEM_ESPECIAL},
        )
        if r.status_code == 429:
            break
    assert r.status_code == 429
    detalhe = r.json()["detail"]
    segundos = int(r.headers["Retry-After"])
    # Formato que o regex de static/i18n.js::translateBackendError espera.
    assert detalhe == f"Muitas requisições. Tente novamente em {segundos}s.", detalhe
