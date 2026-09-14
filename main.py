import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL_ALVO = "https://themosvagas.com.br/regiao/teresina/"
FILE_HISTORICO = "vagas_vistas.json"
MAX_HISTORICO = 500

PALAVRAS_CHAVE = [
    "noturno", "noturna", "12x36", "escala", "fim de semana", 
    "fins de semana", "sábado", "domingo", "feriado", "plantao", 
    "plantão", "madrugada", "17h", "18h", "noite"
]

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Credenciais do Telegram não configuradas.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logging.error(f"Erro ao enviar mensagem no Telegram: {e}")
        return False

def carregar_historico():
    if os.path.exists(FILE_HISTORICO):
        try:
            with open(FILE_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Erro ao ler histórico, criando novo: {e}")
    return []

def salvar_historico(historico):
    historico_limitado = historico[-MAX_HISTORICO:]
    try:
        with open(FILE_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(historico_limitado, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logging.error(f"Erro ao salvar histórico: {e}")

def monitorar_vagas():
    historico = carregar_historico()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        resposta = requests.get(URL_ALVO, headers=headers, timeout=20)
        resposta.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Falha ao acessar o site alvo: {e}")
        return

    soup = BeautifulSoup(resposta.text, "html.parser")
    artigos = soup.find_all("article")

    # Autodiagnóstico: Alerta se o layout do site mudar
    if not artigos:
        logging.warning("Nenhum elemento <article> encontrado. O layout pode ter mudado.")
        enviar_telegram("⚠️ <b>Aviso de Diagnóstico:</b> Nenhuma vaga foi localizada na página principal. É possível que o layout do site tenha sido alterado.")
        return

    novas_vagas = 0
    for artigo in artigos:
        link_tag = artigo.find("a")
        if not link_tag or not link_tag.get("href"):
            continue

        link = urljoin(URL_ALVO, link_tag["href"].strip())
        titulo = link_tag.get_text(strip=True)

        if link in historico:
            continue

        try:
            resp_vaga = requests.get(link, headers=headers, timeout=15)
            if resp_vaga.status_code == 200:
                soup_vaga = BeautifulSoup(resp_vaga.text, "html.parser")
                conteudo_texto = soup_vaga.get_text().lower()

                encontrou = any(p in conteudo_texto or p in titulo.lower() for p in PALAVRAS_CHAVE)

                if encontrou:
                    mensagem = (
                        f"🚨 <b>NOVA VAGA ENCONTRADA!</b>\n\n"
                        f"📌 <b>Título:</b> {titulo}\n"
                        f"🔗 <b>Link:</b> {link}"
                    )
                    enviar_telegram(mensagem)
                    novas_vagas += 1

            historico.append(link)
        except requests.RequestException as e:
            logging.error(f"Erro ao processar a vaga {link}: {e}")

    salvar_historico(historico)
    logging.info(f"Monitoramento concluído. Novas vagas notificadas: {novas_vagas}")

if __name__ == "__main__":
    monitorar_vagas()
