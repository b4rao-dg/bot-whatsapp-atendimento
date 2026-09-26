"""
Conversa com o bot direto no terminal, sem precisar da API do WhatsApp.

Uso:
    python simulador.py                 # usa o horário real
    python simulador.py --fechado       # simula a loja fechada (domingo 22h)
"""

import argparse
from datetime import datetime

from bot.respostas import FUSO, responder


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fechado", action="store_true", help="simula fora do horário")
    args = parser.parse_args()

    agora = datetime(2026, 9, 27, 22, 0, tzinfo=FUSO) if args.fechado else None
    print("Simulador do bot. Digite uma mensagem (ou 'sair').\n")

    while True:
        try:
            mensagem = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if mensagem.lower() == "sair":
            break
        if mensagem:
            print(f"\nBot:\n{responder(mensagem, agora)}\n")


if __name__ == "__main__":
    main()
