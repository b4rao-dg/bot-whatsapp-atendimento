"""
Servidor do bot: recebe as mensagens do WhatsApp (webhook da Meta)
e responde usando as regras de bot/respostas.py.
"""

import hashlib
import hmac
import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, abort, request

from bot.respostas import responder

load_dotenv()

WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]
VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
APP_SECRET = os.getenv("APP_SECRET", "")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v21.0")

URL_ENVIO = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)


def enviar_texto(para: str, texto: str) -> None:
    resposta = requests.post(
        URL_ENVIO,
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": para,
            "type": "text",
            "text": {"body": texto},
        },
        timeout=10,
    )
    if not resposta.ok:
        logging.error("Falha ao enviar para %s: %s", para, resposta.text)


def assinatura_valida(corpo: bytes, assinatura: str) -> bool:
    """Confere se a requisição veio mesmo da Meta (header X-Hub-Signature-256)."""
    if not APP_SECRET:
        return True
    esperado = "sha256=" + hmac.new(APP_SECRET.encode(), corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, assinatura)


@app.get("/webhook")
def verificar_webhook():
    """A Meta chama esta rota uma vez para confirmar que o webhook é nosso."""
    if (request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == VERIFY_TOKEN):
        return request.args.get("hub.challenge", ""), 200
    abort(403)


@app.post("/webhook")
def receber_mensagem():
    if not assinatura_valida(request.get_data(), request.headers.get("X-Hub-Signature-256", "")):
        abort(403)

    dados = request.get_json(silent=True) or {}
    for entrada in dados.get("entry", []):
        for mudanca in entrada.get("changes", []):
            for mensagem in mudanca.get("value", {}).get("messages", []):
                remetente = mensagem["from"]
                if mensagem.get("type") == "text":
                    texto = mensagem["text"]["body"]
                    logging.info("%s: %s", remetente, texto)
                    enviar_texto(remetente, responder(texto))
                else:
                    # áudio, foto, figurinha... o bot não entende, então orienta
                    enviar_texto(remetente, responder("menu"))

    # Sempre 200: se não, a Meta fica reenviando a mesma mensagem
    return "ok", 200


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", 5000)), debug=False)
