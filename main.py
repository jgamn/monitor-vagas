import os
import json
import requests
from bs4 import BeautifulSoup

# Configurações do Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL do site de vagas
URL_ALVO = "https://themosvagas.com.br/regiao/teresina/"

# Palavras-chave para filtro
PALAVRAS_CHAVE = [
    "noturno", "noturna", "12x36", "escala", "fim de semana", 
    "fins de semana", "sábado", "domingo", "feriado", "plantao", 
    "plantão", "madrugada", "17h", "18h", "noite"
]

FILE_HISTORICO = "vagas_vistas.json"

def carregar_historico():
    if os.path.exists(FILE_HISTORICO):
        with open(FILE_HISTORICO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_historico(historico):
    with open(FILE_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    requests.post(url, data=payload)

def monitorar_vagas():
    historico = carregar_historico()

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resposta = requests.get(URL_ALVO, headers=headers)
    
    if resposta.status_code != 200:
        return

    soup = BeautifulSoup(resposta.text, "html.parser")
    artigos = soup.find_all("article")

    for artigo in artigos:
        link_tag = artigo.find("a")
        if not link_tag or not link_tag.get("href"):
            continue

        link = link_tag["href"]
        titulo = link_tag.get_text(strip=True)

        if link in historico:
            continue

        resp_vaga = requests.get(link, headers=headers)
        if resp_vaga.status_code == 200:
            soup_vaga = BeautifulSoup(resp_vaga.text, "html.parser")
            conteudo_texto = soup_vaga.get_text().lower()

            encontrou = any(palavra in conteudo_texto or palavra in titulo.lower() for palavra in PALAVRAS_CHAVE)

            if encontrou:
                mensagem = (
                    f"🚨 <b>NOVA VAGA ENCONTRADA!</b>\n\n"
                    f"📌 <b>Título:</b> {titulo}\n"
                    f"🔗 <b>Link:</b> {link}"
                )
                enviar_telegram(mensagem)

        historico.append(link)

    salvar_historico(historico)

if __name__ == "__main__":
    monitorar_vagas()
