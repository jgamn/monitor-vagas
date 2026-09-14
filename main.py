from playwright.sync_api import sync_playwright

URL = "https://themosvagas.com.br/regiao/teresina/"


def testar_acesso():
    print("=== TESTE DE ACESSO COM PLAYWRIGHT ===")
    print(f"URL: {URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            viewport={
                "width": 1366,
                "height": 768
            }
        )

        try:
            resposta = page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=30000
            )

            if resposta:
                print(f"Status HTTP: {resposta.status}")
            else:
                print("Status HTTP: não informado")

            print(f"URL final: {page.url}")
            print(f"Título da página: {page.title()}")

            quantidade_artigos = page.locator("article").count()
            print(f"Quantidade de <article>: {quantidade_artigos}")

            print("\n=== PRIMEIRAS VAGAS ENCONTRADAS ===")

            limite = min(5, quantidade_artigos)

            for i in range(limite):
                artigo = page.locator("article").nth(i)

                try:
                    texto = artigo.inner_text().strip()
                    texto = " ".join(texto.split())

                    print(f"\nVaga {i + 1}:")
                    print(texto[:500])

                except Exception as erro:
                    print(f"Erro ao ler a vaga {i + 1}: {erro}")

            print("\n=== FIM DO TESTE ===")

        except Exception as erro:
            print("\nERRO DURANTE O ACESSO:")
            print(erro)

        finally:
            browser.close()


if __name__ == "__main__":
    testar_acesso()
