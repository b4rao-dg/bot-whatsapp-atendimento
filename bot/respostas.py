"""
Regras de atendimento da loja fictícia "Doce Encanto Confeitaria".

Fica separado da API do WhatsApp de propósito: aqui é só texto entrando e
texto saindo, então dá para testar no terminal e com pytest.
"""

import re
import unicodedata
from datetime import datetime, time
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")
LOJA = "Doce Encanto Confeitaria"

# dia da semana (0 = segunda) -> (abre, fecha). Domingo fechado.
HORARIOS = {
    0: (time(9), time(18)),
    1: (time(9), time(18)),
    2: (time(9), time(18)),
    3: (time(9), time(18)),
    4: (time(9), time(18)),
    5: (time(9), time(13)),
}

MENU = (
    f"Olá! 👋 Bem-vindo(a) à *{LOJA}*.\n"
    "Digite o número da opção:\n\n"
    "1️⃣ Cardápio e preços\n"
    "2️⃣ Fazer uma encomenda\n"
    "3️⃣ Entrega e retirada\n"
    "4️⃣ Formas de pagamento\n"
    "5️⃣ Horário e endereço\n"
    "6️⃣ Falar com um atendente"
)

CARDAPIO = (
    "🍰 *Cardápio*\n\n"
    "• Bolo de pote: R$ 12,00\n"
    "• Fatia de bolo: R$ 14,00\n"
    "• Brigadeiro gourmet (cento): R$ 180,00\n"
    "• Bolo inteiro 1 kg: a partir de R$ 90,00\n"
    "• Torta de limão (inteira): R$ 75,00\n\n"
    "Digite *2* para encomendar ou *menu* para voltar."
)

ENCOMENDA = (
    "📝 *Encomendas*\n\n"
    "Encomendas de bolos e docinhos precisam de *48h de antecedência*.\n"
    "Mande numa mensagem só:\n"
    "1. O que deseja e a quantidade\n"
    "2. Data e horário\n"
    "3. Retirada ou entrega (com endereço)\n\n"
    "Um atendente confirma o valor final em seguida. 😊"
)

ENTREGA = (
    "🛵 *Entrega e retirada*\n\n"
    "• Retirada na loja: grátis\n"
    "• Entrega até 5 km: R$ 8,00\n"
    "• Entrega de 5 a 10 km: R$ 15,00\n\n"
    "Entregamos de terça a sábado."
)

PAGAMENTO = (
    "💳 *Formas de pagamento*\n\n"
    "• Pix (chave: CNPJ 00.000.000/0001-00)\n"
    "• Cartão de crédito e débito\n"
    "• Dinheiro na retirada\n\n"
    "Encomendas: 50% de sinal no Pix para confirmar."
)

ENDERECO = (
    "📍 *Horário e endereço*\n\n"
    "Rua das Flores, 123, Centro\n\n"
    "Segunda a sexta: 9h às 18h\n"
    "Sábado: 9h às 13h\n"
    "Domingo: fechado"
)

ATENDENTE = (
    "👩‍💼 Certo! Já avisei nossa equipe. Um atendente vai te responder "
    "por aqui em instantes."
)

NAO_ENTENDI = (
    "Desculpe, não entendi. 🤔\n"
    "Digite *menu* para ver as opções."
)

FORA_DO_HORARIO = (
    f"Olá! A *{LOJA}* está fechada agora. 🌙\n\n"
    "Nosso horário: seg a sex das 9h às 18h e sábado das 9h às 13h.\n"
    "Deixe sua mensagem que respondemos assim que abrirmos!\n\n"
    "Enquanto isso, você já pode ver o *cardápio* digitando 1."
)

OPCOES = {
    "1": CARDAPIO,
    "2": ENCOMENDA,
    "3": ENTREGA,
    "4": PAGAMENTO,
    "5": ENDERECO,
    "6": ATENDENTE,
}

# palavra-chave -> resposta. As palavras já estão sem acento e minúsculas.
PALAVRAS_CHAVE = {
    ("cardapio", "preco", "valor", "quanto custa", "bolo", "brigadeiro", "torta"): CARDAPIO,
    ("encomenda", "encomendar", "pedido", "festa", "aniversario"): ENCOMENDA,
    ("entrega", "entregam", "frete", "delivery", "retirada", "retirar"): ENTREGA,
    ("pix", "cartao", "pagamento", "pagar", "dinheiro"): PAGAMENTO,
    ("endereco", "onde fica", "localizacao", "horario", "abre", "fecha"): ENDERECO,
    ("atendente", "humano", "pessoa", "falar com"): ATENDENTE,
}

INFORMATIVAS = (CARDAPIO, ENTREGA, PAGAMENTO, ENDERECO)

SAUDACOES = ("oi", "ola", "menu", "inicio", "bom dia", "boa tarde", "boa noite", "opa", "eai")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem pontuação: 'Oi, Cartão?' -> 'oi cartao'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    sem_pontuacao = re.sub(r"[^\w\s]", " ", sem_acento)
    return " ".join(sem_pontuacao.lower().split())


def loja_aberta(agora: datetime) -> bool:
    horario = HORARIOS.get(agora.weekday())
    if horario is None:
        return False
    abre, fecha = horario
    return abre <= agora.time() < fecha


def _buscar_palavra_chave(texto: str) -> str | None:
    for palavras, resposta in PALAVRAS_CHAVE.items():
        if any(p in texto for p in palavras):
            return resposta
    return None


def _eh_saudacao(texto: str) -> bool:
    return texto in SAUDACOES or any(texto.startswith(s + " ") for s in SAUDACOES)


def responder(mensagem: str, agora: datetime | None = None) -> str:
    agora = agora or datetime.now(FUSO)
    texto = normalizar(mensagem)

    resposta = OPCOES.get(texto) or _buscar_palavra_chave(texto)
    if resposta is None and _eh_saudacao(texto):
        resposta = MENU

    # Fora do horário, informações simples continuam respondendo na hora;
    # o que precisa de uma pessoa (encomenda, atendente) recebe o aviso.
    if not loja_aberta(agora) and resposta not in INFORMATIVAS:
        return FORA_DO_HORARIO

    return resposta or NAO_ENTENDI
