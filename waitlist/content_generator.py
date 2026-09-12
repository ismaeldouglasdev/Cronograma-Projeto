#!/usr/bin/env python3
"""
Gerador de Conteudo - Cronograma Pro
Gera posts prontos para redes sociais (Instagram, TikTok, Twitter/X).
Uso: python content_generator.py --type tip --platform instagram
"""

import argparse
import random
import textwrap
from datetime import datetime, timedelta

# =============================================================================
# BANCO DE HASHTAGS
# =============================================================================
HASHTAGS = {
    "estudo": [
        "#estudar", "#prova", "#universidade", "#faculdade",
        "#estudos", "#dicasdeestudo", "#materiaisdeestudo",
    ],
    "produtividade": [
        "#produtividade", "#foco", "#pomodoro", "#rotina",
        "#gestaodetempo", "#organizacao", "#planejamento",
    ],
    "cronograma_pro": [
        "#cronogramapro", "#estudecomgamificacao", "#cronogramaproSaaS",
    ],
    "estudante_br": [
        "#estudantebr", "#vestibular", "#enem", "#concurseiro",
        "#estudantebem", "#motivacaoestudo", "#vidadeestudante",
    ],
}

# =============================================================================
# TEMPLATES POR TIPO DE CONTEUDO
# =============================================================================
# Cada template tem: caption, hashtags (categorias), melhor_horario
# Variaveis em {chaves} sao preenchidas randomicamente

TIPS = [
    {
        "caption": (
            "PODCAST ESCUTADO ENQUANTO ESTUDA? Tente ouvir podcasts de educacao "
            "enquanto caminha ou faz exercicios. O conteudo reforca o que voce ja "
            "estudou e aproveita o tempo ocioso.\n\n"
            "Quer um metodo pra organizar TUDO isso? -> link na bio"
        ),
        "hashtags": ["estudo", "produtividade", "estudante_br"],
        "horario": "08:00 - 09:00",
        "plataforma": ["instagram", "twitter"],
    },
    {
        "caption": (
            "PROVA AMANHA? Nao entre em panico.\n\n"
            "1. Revisa so os pontos-chave\n"
            "2. Faz simulados dos ultimos anos\n"
            "3. Dorme bem (de verdade)\n\n"
            "Metodo comprovado: revisao espacada. O Cronograma Pro faz isso "
            "por voce automaticamente."
        ),
        "hashtags": ["estudo", "estudante_br", "cronograma_pro"],
        "horario": "19:00 - 20:00",
        "plataforma": ["tiktok", "twitter"],
    },
    {
        "caption": (
            "VAZIO MENTAL? Quando a cabeca travar, muda de materia.\n\n"
            "Estudar a mesma coisa por horas gera fadiga cognitiva. "
            "Alterne entre materias diferentes pra manter o cerebro ativo.\n\n"
            "O Cronograma Pro alterna automaticamente pra voce."
        ),
        "hashtags": ["produtividade", "estudo"],
        "horario": "12:00 - 13:00",
        "plataforma": ["instagram", "tiktok"],
    },
    {
        "caption": (
            "MAPA MENTAL: desenha o conteudo antes de decorar.\n\n"
            "Criar um mapa mental ativa areas do cerebro que leitura passiva "
            "nao atinge. Voce aprende MUITO mais rapido.\n\n"
            "Ferramenta que organiza tudo: link na bio"
        ),
        "hashtags": ["estudo", "produtividade", "estudante_br"],
        "horario": "07:00 - 08:00",
        "plataforma": ["instagram", "tiktok"],
    },
    {
        "caption": (
            "POMODORO FUNCTIONAL: 25 min focado + 5 min descanso.\n\n"
            "NAO adianta ficar 4 horas sentado olhando pro caderno. "
            "Intervalos curtos mantem a concentracao alta.\n\n"
            "Testa e me conta nos comentarios se funcionou pra voce."
        ),
        "hashtags": ["produtividade", "pomodoro", "estudo"],
        "horario": "10:00 - 11:00",
        "plataforma": ["instagram", "twitter"],
    },
    {
        "caption": (
            "ERREU A PROVA? O erro e seu MELHOR professor.\n\n"
            "Cada erro revela uma lacuna. Anota o erro, entende o por que errou, "
            "e revisa esse ponto em 1 dia, 7 dias e 30 dias.\n\n"
            "Isso se chama revisao espacada. O Cronograma Pro faz isso "
            "automaticamente."
        ),
        "hashtags": ["estudo", "estudante_br", "cronograma_pro"],
        "horario": "20:00 - 21:00",
        "plataforma": ["tiktok", "twitter"],
    },
    {
        "caption": (
            "CELULAR DISTRAINDO? Coloca no modo aviao durante os estudos.\n\n"
            "Um simples notificacao quebra seu foco por 23 minutos em media. "
            "23 MINUTOS. Isso e quase um Pomodoro inteiro perdido.\n\n"
            "Resolveu? Me conta aqui"
        ),
        "hashtags": ["produtividade", "foco", "estudante_br"],
        "horario": "09:00 - 10:00",
        "plataforma": ["tiktok", "instagram"],
    },
    {
        "caption": (
            "ENEM/SIMULADO: comeca pelas questoes que voce MANJA.\n\n"
            "Resgata as certezas primeiro pra ganhar confianca e marcar tempo. "
            "Depois ataca as duvidas. Estrategia > esforco cego."
        ),
        "hashtags": ["estudante_br", "enem", "vestibular", "estudo"],
        "horario": "14:00 - 15:00",
        "plataforma": ["twitter", "instagram"],
    },
]

MEMES = [
    {
        "caption": (
            "eu quando a pessoa fala que nao precisa de cronograma:\n\n"
            " 08:00 - estudar tudo\n"
            " 08:05 - celular\n"
            " 08:06 - acordar no dia seguinte\n\n"
            "isso so tem um jeito: cronogramapro.com"
        ),
        "hashtags": ["estudante_br", "memedeestudo", "estudo"],
        "horario": "12:00 - 13:00",
        "plataforma": ["tiktok", "instagram"],
    },
    {
        "caption": (
            "nivel de foco do estudante antes da prova:\n"
            " - semana 1: eu vou passar em tudo\n"
            " - semana 2: bom pelo menos em uma\n"
            " - vespera: eu vou reparar o mundo com meus erros\n\n"
            "imagine ter um cronograma automatizado... cronogramapro.com"
        ),
        "hashtags": ["estudante_br", "memedeestudo", "enem"],
        "horario": "18:00 - 19:00",
        "plataforma": ["tiktok", "twitter"],
    },
    {
        "caption": (
            "eu: vou estudar 6 horas hoje\n\n"
            "horas depois:\n"
            " - 20 min lendo\n"
            " - 1h no tiktok\n"
            " - 40 min comendo\n"
            " - 20 min reclamando que nao estudei\n\n"
            "o cronogramapro resolve esse ciclo. de verdade."
        ),
        "hashtags": ["estudante_br", "memedeestudo", "produtividade"],
        "horario": "20:00 - 21:00",
        "plataforma": ["tiktok", "instagram"],
    },
    {
        "caption": (
            "como eu me vejo estudando vs como eu realmente estudo:\n\n"
            "imagem 1: foco total, caderno organizado, cafe na mao\n"
            "imagem 2: jogado na cama com o celular na cara\n\n"
            "foco real tem jeito: cronogramapro.com"
        ),
        "hashtags": ["memedeestudo", "estudante_br"],
        "horario": "11:00 - 12:00",
        "plataforma": ["instagram", "tiktok"],
    },
    {
        "caption": (
            "POV: voce tem um cronograma perfeito no papel\n\n"
            " segunda: historia\n"
            " terca: matematica\n"
            " quarta: (ja desistiu)\n\n"
            " cronograma na cabeca nao funciona.\n"
            " cronogramapro.com - funciona."
        ),
        "hashtags": ["estudante_br", "memedeestudo", "cronograma_pro"],
        "horario": "17:00 - 18:00",
        "plataforma": ["tiktok", "twitter"],
    },
]

ANNOUNCEMENTS = [
    {
        "caption": (
            "O CRONOGRAMA PRO TA CHEGANDO!\n\n"
            "Uma ferramenta que monta seu cronograma de estudos AUTOMATICAMENTE "
            "baseado no seu edital/prova.\n\n"
            "Enquanto isso: entra na waitlist e garanta acesso antecipado.\n"
            "Link na bio"
        ),
        "hashtags": ["cronograma_pro", "estudante_br", "produtividade"],
        "horario": "10:00 - 11:00",
        "plataforma": ["instagram", "twitter"],
    },
    {
        "caption": (
            "NOVIDADE: o Cronograma Pro sera GAMIFICADO.\n\n"
            "XP por materia, niveis de estudo, conquistas desbloqueaveis.\n"
            "Estudar nunca mais vai ser a mesma coisa.\n\n"
            "Garanta vaga na waitlist"
        ),
        "hashtags": ["cronograma_pro", "gamificacao", "estudante_br"],
        "horario": "19:00 - 20:00",
        "plataforma": ["tiktok", "instagram"],
    },
    {
        "caption": (
            "BATEU A META DE X NA WAITLIST!\n\n"
            "Obrigado a todos que ja entraram. Cada pessoa que entra e mais "
            "pessoa perto da prova dos sonhos.\n\n"
            "Compartilha com aquele amigo que precisa disso."
        ),
        "hashtags": ["cronograma_pro", "estudante_br"],
        "horario": "12:00 - 13:00",
        "plataforma": ["instagram", "twitter", "tiktok"],
    },
    {
        "caption": (
            "PRIMEIRO PASSO: o Cronograma Pro vai sugerir materias com base "
            "no tempo restante ate sua prova.\n\n"
            "Mais tempo = mais materias. Menos tempo = foco no que mais cai.\n\n"
            "Simple. Effective. Automatizado."
        ),
        "hashtags": ["cronograma_pro", "estudo", "produtividade"],
        "horario": "08:00 - 09:00",
        "plataforma": ["instagram", "twitter"],
    },
]

QUESTIONS = [
    {
        "caption": (
            "POLL STORY:\n\n"
            "Quanto tempo voce ESTUDA por dia de verdade?\n\n"
            "A) Menos de 1 hora\n"
            "B) 1 a 3 horas\n"
            "C) 3 a 5 horas\n"
            "D) Mais de 5 horas\n\n"
            "Comenta o resultado - curioso pra saber!"
        ),
        "hashtags": ["estudante_br", "estudo", "produtividade"],
        "horario": "10:00 - 11:00",
        "plataforma": ["instagram", "tiktok"],
    },
    {
        "caption": (
            "PERGUNTA PRA STORIES:\n\n"
            "Qual materia voce MAIS dificuldade?\n\n"
            "Me manda no direct que eu te dou uma dica personalizada!"
        ),
        "hashtags": ["estudante_br", "estudo"],
        "horario": "16:00 - 17:00",
        "plataforma": ["instagram"],
    },
    {
        "caption": (
            "TOGGLE STORY:\n\n"
            "Voce ja tentou montar um cronograma de estudos sozinho?\n\n"
            " sim / ja desisti em 3 dias\n\n"
            "se respondeu segunda opcao... cronogramapro.com te espera"
        ),
        "hashtags": ["estudante_br", "cronograma_pro"],
        "horario": "20:00 - 21:00",
        "plataforma": ["instagram", "tiktok"],
    },
    {
        "caption": (
            "QUIZ STORY:\n\n"
            "Quantos anos um estudante perde em media tentando organizar "
            "estudos manualmente?\n\n"
            "A) 0 - nunca perde tempo\n"
            "B) 6 meses\n"
            "C) 1 ano\n"
            "D) mais do que imagina\n\n"
            "Resposta no proximo slide"
        ),
        "hashtags": ["estudante_br", "produtividade"],
        "horario": "11:00 - 12:00",
        "plataforma": ["instagram"],
    },
    {
        "caption": (
            "HOT TAKE:\n\n"
            "Organizar cronograma no Excel e a mesma coisa que planilha "
            "de gastos: voce faz uma vez e nunca mais olha.\n\n"
            "Concorda ou discorda? Comenta"
        ),
        "hashtags": ["estudante_br", "memedeestudo", "cronograma_pro"],
        "horario": "18:00 - 19:00",
        "plataforma": ["twitter", "instagram"],
    },
]

TESTIMONIALS = [
    {
        "caption": (
            "EXEMPLO DE DEPOIMENTO (criado para demonstracao)\n\n"
            "Nunca tinha conseguido manter um cronograma por mais de 2 semanas. "
            "Com o Cronograma Pro, nao preciso pensar - ele monta e eu so sigo. "
            "Me sinto muito mais organizada.\n"
            "  Maria, 22 anos, estudando para concursos\n\n"
            "#depoimento #cronogramapro #estudantebr"
        ),
        "hashtags": ["cronograma_pro", "estudante_br"],
        "horario": "09:00 - 10:00",
        "plataforma": ["instagram"],
    },
    {
        "caption": (
            "EXEMPLO DE DEPOIMENTO (criado para demonstracao)\n\n"
            "Eu tentava montar cronograma no notion e no excel. Nada funcionava. "
            "O Cronograma Pro fez em 2 minutos o que eu nao consegui em 2 anos. "
            "Simples assim.\n"
            "  Pedro, 20 anos, vestibulando\n\n"
            "#depoimento #cronogramapro"
        ),
        "hashtags": ["cronograma_pro", "estudante_br", "vestibular"],
        "horario": "15:00 - 16:00",
        "plataforma": ["instagram", "tiktok"],
    },
    {
        "caption": (
            "EXEMPLO DE DEPOIMENTO (criado para demonstracao)\n\n"
            "A gamificacao me manteve motivada por 3 meses seguidos. Eu nunca "
            "estudei tanto na vida. O XP e as conquistas sao viciantes.\n"
            "  Ana, 19 anos, estudando para o ENEM\n\n"
            "#depoimento #cronogramapro #enem"
        ),
        "hashtags": ["cronograma_pro", "enem", "estudante_br"],
        "horario": "13:00 - 14:00",
        "plataforma": ["tiktok", "instagram"],
    },
]

# Mapeia tipo de conteudo -> lista de templates
CONTENT_MAP = {
    "tip": TIPS,
    "meme": MEMES,
    "announcement": ANNOUNCEMENTS,
    "question": QUESTIONS,
    "testimonial": TESTIMONIALS,
}

# =============================================================================
# FORMATACAO POR PLATAFORMA
# =============================================================================

PLATFORM_LIMITS = {
    "instagram": {"max_caption": 2200, "max_hashtags": 30, "emoji": True},
    "tiktok": {"max_caption": 2200, "max_hashtags": 15, "emoji": True},
    "twitter": {"max_caption": 280, "max_hashtags": 5, "emoji": False},
}


def selecionar_hashtags(categorias: list[str], limite: int) -> str:
    """Seleciona hashtags aleatorias das categorias indicadas."""
    pool = []
    for cat in categorias:
        pool.extend(HASHTAGS.get(cat, []))
    random.shuffle(pool)
    return " ".join(pool[:limite])


def formatar_para_plataforma(template: dict, plataforma: str) -> str:
    """Formata o conteudo de acordo com as regras da plataforma."""
    config = PLATFORM_LIMITS.get(plataforma, PLATFORM_LIMITS["instagram"])
    caption = template["caption"]

    # Adiciona emoji no titulo se plataforma suporta
    if config["emoji"]:
        caption = caption

    # Hashtags
    num_hashtags = min(len(template["hashtags"]) * 3, config["max_hashtags"])
    tags = selecionar_hashtags(template["hashtags"], num_hashtags)

    # Limite de caracteres no Twitter
    if plataforma == "twitter":
        hashtags_line = "\n\n" + tags if tags else ""
        if len(caption) + len(hashtags_line) > config["max_caption"]:
            caption = caption[: config["max_caption"] - len(hashtags_line) - 3] + "..."
        return caption + hashtags_line

    # Instagram e TikTok: hashtags embaixo
    resultado = caption
    if tags:
        resultado += "\n\n" + tags

    return resultado


def gerar_post(tipo: str, plataforma: str) -> str:
    """Gera um post aleatorio do tipo informado para a plataforma."""
    templates = CONTENT_MAP.get(tipo)
    if not templates:
        return f"Tipo '{tipo}' nao encontrado. Tipos validos: {', '.join(CONTENT_MAP.keys())}"

    # Filtra por plataforma (se o template tem restricao de plataforma)
    candidatos = [
        t for t in templates
        if "plataforma" not in t or plataforma in t["plataforma"]
    ]
    if not candidatos:
        # Se nenhum filtrado, pega todos
        candidatos = templates

    template = random.choice(candidatos)
    conteudo = formatar_para_plataforma(template, plataforma)

    horario = template.get("horario", "variavel")

    separator = "=" * 60
    header = f"CRONOGRAMA PRO - POST [{tipo.upper()}] [{plataforma.upper()}]"
    time_info = f"Melhor horario para postar: {horario}"
    type_info = f"Tipo: {tipo}"

    return (
        f"{separator}\n"
        f"{header}\n"
        f"{time_info}\n"
        f"{type_info}\n"
        f"{separator}\n\n"
        f"{conteudo}\n\n"
        f"{separator}\n"
        f"Pronto para copiar e colar!\n"
        f"{separator}"
    )


def gerar_calendario(dias: int = 7, plataforma: str = "instagram") -> str:
    """Gera um plano de conteudo para N dias."""
    tipos_disponiveis = ["tip", "meme", "question", "tip", "announcement", "meme", "testimonial"]
    hoje = datetime.now()

    linhas = []
    separator = "=" * 60
    linhas.append(separator)
    linhas.append(f"CRONOGRAMA DE CONTEUDO - PROXIMOS {dias} DIAS")
    linhas.append(f"Plataforma: {plataforma.upper()}")
    linhas.append(f"Gerado em: {hoje.strftime('%d/%m/%Y %H:%M')}")
    linhas.append(separator)
    linhas.append("")

    for i in range(dias):
        data = hoje + timedelta(days=i)
        tipo = tipos_disponiveis[i % len(tipos_disponiveis)]
        templates = CONTENT_MAP.get(tipo, TIPS)

        candidatos = [
            t for t in templates
            if "plataforma" not in t or plataforma in t["plataforma"]
        ]
        if not candidatos:
            candidatos = templates

        template = random.choice(candidatos)
        conteudo = formatar_para_plataforma(template, plataforma)

        dia_semana = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]
        nome_dia = dia_semana[data.weekday()]
        horario = template.get("horario", "variavel")

        linhas.append(f"DIA {i + 1} - {data.strftime('%d/%m')} ({nome_dia})")
        linhas.append(f"Tipo: {tipo.upper()} | Horario: {horario}")
        linhas.append("-" * 40)
        linhas.append(conteudo)
        linhas.append("")
        linhas.append("")

    linhas.append(separator)
    linhas.append("FIM DO CALENDARIO")
    linhas.append(separator)

    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de conteudo para redes sociais - Cronograma Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exemplos de uso:
              python content_generator.py --type tip --platform instagram
              python content_generator.py --type meme --platform tiktok
              python content_generator.py --type announcement --platform twitter
              python content_generator.py --calendar
              python content_generator.py --calendar --days 14 --platform tiktok
              python content_generator.py --list-types
        """),
    )

    parser.add_argument(
        "--type", "-t",
        choices=list(CONTENT_MAP.keys()),
        help="Tipo de conteudo (tip, meme, announcement, question, testimonial)",
    )
    parser.add_argument(
        "--platform", "-p",
        choices=["instagram", "tiktok", "twitter"],
        default="instagram",
        help="Plataforma alvo (padrao: instagram)",
    )
    parser.add_argument(
        "--calendar", "-c",
        action="store_true",
        help="Gera um calendario de conteudo para N dias",
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=7,
        help="Numero de dias para o calendario (padrao: 7)",
    )
    parser.add_argument(
        "--list-types", "-l",
        action="store_true",
        help="Lista os tipos de conteudo disponiveis",
    )

    args = parser.parse_args()

    # Lista tipos disponiveis
    if args.list_types:
        print("Tipos de conteudo disponiveis:")
        for tipo, templates in CONTENT_MAP.items():
            print(f"  {tipo:15} - {len(templates)} templates")
        print(f"\nPlataformas: instagram, tiktok, twitter")
        return

    # Gera calendario
    if args.calendar:
        print(gerar_calendario(args.days, args.platform))
        return

    # Gera post individual
    if args.type:
        print(gerar_post(args.type, args.platform))
        return

    # Nenhum argumento: mostra ajuda
    parser.print_help()


if __name__ == "__main__":
    main()
