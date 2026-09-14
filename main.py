import os
import json
import re
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAGINAS_PARA_VERIFICAR = 3
FILE_HISTORICO = "vagas_vistas.json"

# Terrmos diretos de turnos noturnos/flexíveis/fins de semana
TERMOS_NOTURNOS = [
    "noturno", "noturna", "12x36", "madrugada", "fechamento", 
    "fim de semana", "fins de semana", "sábado", "sabado", 
    "domingo", "escala", "plantao", "plantão", "part-time", "meio periodo"
]

# Cargos que frequentemente possuem escala noturna/fim de semana (para anúncios genéricos)
CARGOS_SUSPEITOS = [
    "atendente", "recepcionista", "garcom", "garçom", "garçonete", 
    "cozinha", "auxiliar de cozinha", "pizzaiolo", "entregador", 
    "vigilante", "porteiro", "operador", "caixa", "atendimento", "farmacia", "farmácia"
]

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

def eh_vaga_compativel(titulo, texto_completo):
    texto_lower = texto_completo.lower()
    titulo_lower = titulo.lower()

    # 1. Checa presença de termos noturnos explícitos
    if any(termo in texto_lower or termo in titulo_lower for termo in TERMOS_NOTURNOS):
        return True

    # 2. Avalia horários numéricos via Regex (ex: 18h, 18:00, 19h30, 22:00)
    # Procura horários de início noturno a partir de 17:30 / 18:00
    padrao_horario_noturno = r'(1[8-9]|2[0-3])\s*(h|:|hrs|horas)'
    if re.search(padrao_horario_noturno, texto_lower):
        return True

    # 3. Se for anúncio genérico ("44h", "a combinar"), analisa se o cargo costuma ter turno noturno
    if any(cargo in titulo_lower for cargo in CARGOS_SUSPEITOS):
        # Se não for expressamente uma vaga comercial de escritório (ex: 08:00 às 18:00), envia para checagem
        if not re.search(r'(0[7-9]|10)\s*(h|:).*as.*\s*(1[7-8])\s*(h|:)', texto_lower):
            return True

    return False

def monitorar_vagas():
    historico = carregar_historico()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for pagina in range(1, PAGINAS_PARA_VERIFICAR + 1):
        url = "https://themosvagas.com.br/regiao/teresina/" if pagina == 1 else f"https://themosvagas.com.br/regiao/teresina/page/{pagina}/"
        resposta = requests.get(url, headers=headers)
        
        if resposta.status_code != 200:
            continue

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
                conteudo_texto = soup_vaga.get_text()

                if eh_vaga_compativel(titulo, conteudo_texto):
                    mensagem = (
                        f"🚨 <b>OPORTUNIDADE ENCONTRADA!</b>\n\n"
                        f"📌 <b>Título:</b> {titulo}\n"
                        f"🔗 <b>Link:</b> {link}"
                    )
                    enviar_telegram(mensagem)

            historico.append(link)

    salvar_historico(historico)

if __name__ == "__main__":
    monitorar_vagas()
