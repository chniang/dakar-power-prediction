"""
Génération automatique des captures d'écran — Dakar Power Prediction
Cible : Space HF https://tijaani-dakar-power-prediction.hf.space/
Usage  : python scripts/take_screenshots.py
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

SPACE_URL  = "https://tijaani-dakar-power-prediction.hf.space/"
IMAGES_DIR = Path(__file__).parent.parent / "images"
VIEWPORT   = {"width": 1920, "height": 1080}


async def wait_streamlit(page):
    """Attend que Streamlit soit complètement rendu (DOM + réseau + Plotly)."""
    await page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=90_000)
    # Laisse le WebSocket Streamlit s'établir et les composants se monter
    await asyncio.sleep(4)
    # Si un spinner tourne encore, on attend qu'il disparaisse
    try:
        await page.wait_for_selector(
            '[data-testid="stSpinner"]', state="hidden", timeout=15_000
        )
    except PWTimeout:
        pass
    await asyncio.sleep(2)


async def wait_plotly(page, timeout=20_000):
    """Attend qu'au moins un graphique Plotly soit rendu."""
    await page.wait_for_selector(".js-plotly-plot", timeout=timeout)
    # Plotly anime ses graphiques — on attend la fin du paint
    await asyncio.sleep(3)


async def click_tab(page, index: int):
    """Clique sur l'onglet Streamlit à l'index donné (0-based) et attend le rendu."""
    tabs = page.get_by_role("tab")
    await tabs.nth(index).click()
    await asyncio.sleep(1)
    try:
        await page.wait_for_selector(
            '[data-testid="stSpinner"]', state="hidden", timeout=10_000
        )
    except PWTimeout:
        pass
    await asyncio.sleep(2)


async def main():
    IMAGES_DIR.mkdir(exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            channel="chrome",   # utilise Chrome système — hérite du réseau Windows
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(viewport=VIEWPORT)

        # ── Chargement initial ──────────────────────────────────────────────
        print(f"-> Ouverture du Space : {SPACE_URL}")
        await page.goto(SPACE_URL, wait_until="domcontentloaded", timeout=90_000)
        await wait_streamlit(page)
        print("  OK Streamlit prêt\n")

        # ── 1. Prédiction ───────────────────────────────────────────────────
        print("-> [1/3] prediction.png")
        # L'onglet Prédiction est actif par défaut — on lance une prédiction
        btn_pred = page.get_by_role("button", name="Lancer la Prédiction")
        await btn_pred.click()
        await wait_plotly(page)          # attend la jauge Plotly
        await asyncio.sleep(1)           # marge pour le paint final
        await page.screenshot(path=str(IMAGES_DIR / "prediction.png"))
        print("  OK images/prediction.png\n")

        # ── 2. Carte ────────────────────────────────────────────────────────
        print("-> [2/3] carte.png")
        await click_tab(page, 1)         # index 1 = 🗺️ Carte
        await asyncio.sleep(4)
        # Si le map Plotly est déjà là (session réutilisée), on le prend directement.
        # Sinon on clique le bouton via JavaScript pour contourner l'emoji dans le sélecteur.
        map_present = await page.locator(".js-plotly-plot").count()
        if map_present == 0:
            print("  -> map absente, clic bouton via JS...")
            await page.evaluate("""
                () => {
                    const btns = [...document.querySelectorAll('button')];
                    const btn = btns.find(b => b.innerText.includes('Calculer'));
                    if (btn) btn.click();
                }
            """)
            await wait_plotly(page, timeout=40_000)
        else:
            print("  -> map deja rendue, capture directe")
            await asyncio.sleep(2)
        await page.screenshot(path=str(IMAGES_DIR / "carte.png"))
        print("  OK images/carte.png\n")

        # ── 3. Statistiques ─────────────────────────────────────────────────
        print("-> [3/3] analytics.png")
        await click_tab(page, 2)         # index 2 = 📊 Statistiques
        # Le tab Streamlit charge le CSV + bar chart automatiquement.
        # On attend via le dataframe (st.dataframe) plutôt que Plotly
        # pour éviter de matcher les 8 graphiques cachés des tabs précédents.
        try:
            await page.wait_for_selector(
                '[data-testid="stDataFrame"]', timeout=20_000
            )
        except PWTimeout:
            pass  # Si pas de dataframe visible, on screenshot quand même
        await asyncio.sleep(4)   # Laisse le bar chart finir son rendu
        await page.screenshot(path=str(IMAGES_DIR / "analytics.png"))
        print("  OK images/analytics.png\n")

        await browser.close()

    print("OK Toutes les captures générées dans images/")


if __name__ == "__main__":
    asyncio.run(main())
