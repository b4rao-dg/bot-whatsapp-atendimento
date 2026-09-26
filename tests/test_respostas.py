from datetime import datetime

import pytest

from bot.respostas import (
    ATENDENTE, CARDAPIO, ENCOMENDA, ENDERECO, ENTREGA, FORA_DO_HORARIO, FUSO,
    MENU, NAO_ENTENDI, PAGAMENTO, loja_aberta, normalizar, responder,
)

# 2026-09-23 é quarta-feira; 2026-09-26 é sábado; 2026-09-27 é domingo
QUARTA_14H = datetime(2026, 9, 23, 14, 0, tzinfo=FUSO)
QUARTA_20H = datetime(2026, 9, 23, 20, 0, tzinfo=FUSO)
SABADO_12H = datetime(2026, 9, 26, 12, 0, tzinfo=FUSO)
SABADO_14H = datetime(2026, 9, 26, 14, 0, tzinfo=FUSO)
DOMINGO_10H = datetime(2026, 9, 27, 10, 0, tzinfo=FUSO)


def test_normalizar_tira_acento_e_maiuscula():
    assert normalizar("  Cartão de CRÉDITO? ") == "cartao de credito"


@pytest.mark.parametrize("agora, esperado", [
    (QUARTA_14H, True),
    (QUARTA_20H, False),
    (SABADO_12H, True),
    (SABADO_14H, False),
    (DOMINGO_10H, False),
])
def test_horario_de_funcionamento(agora, esperado):
    assert loja_aberta(agora) is esperado


@pytest.mark.parametrize("mensagem", ["oi", "Olá", "Bom dia!", "menu", "Oi, tudo bem?"])
def test_saudacao_mostra_menu(mensagem):
    assert responder(mensagem, QUARTA_14H) == MENU


@pytest.mark.parametrize("opcao, esperado", [
    ("1", CARDAPIO), ("2", ENCOMENDA), ("3", ENTREGA),
    ("4", PAGAMENTO), ("5", ENDERECO), ("6", ATENDENTE),
])
def test_opcoes_do_menu(opcao, esperado):
    assert responder(opcao, QUARTA_14H) == esperado


@pytest.mark.parametrize("mensagem, esperado", [
    ("Quanto custa o bolo de pote?", CARDAPIO),
    ("vocês entregam no meu bairro?", ENTREGA),
    ("aceita PIX?", PAGAMENTO),
    ("qual o endereço", ENDERECO),
    ("quero fazer uma encomenda", ENCOMENDA),
    ("quero falar com um atendente", ATENDENTE),
])
def test_palavras_chave(mensagem, esperado):
    assert responder(mensagem, QUARTA_14H) == esperado


def test_mensagem_desconhecida():
    assert responder("asdfgh", QUARTA_14H) == NAO_ENTENDI


@pytest.mark.parametrize("mensagem", ["oi", "2", "6", "quero uma encomenda", "asdfgh"])
def test_fora_do_horario_avisa_que_esta_fechado(mensagem):
    assert responder(mensagem, DOMINGO_10H) == FORA_DO_HORARIO


@pytest.mark.parametrize("mensagem, esperado", [
    ("1", CARDAPIO), ("qual o endereço", ENDERECO), ("aceita pix", PAGAMENTO),
])
def test_fora_do_horario_informacoes_continuam_respondendo(mensagem, esperado):
    assert responder(mensagem, DOMINGO_10H) == esperado
