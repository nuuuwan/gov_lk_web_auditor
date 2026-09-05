from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from .Coverage import CoverageCalculator
from .FlowStore import FlowStore
from .OpenAIFlowDiscovery import OpenAIFlowDiscovery
from .Provenance import classify


class TranslationVerifier:
    LANGUAGES = ("en", "si", "ta")

    def __init__(self, flow_dir: Path = Path("translation.flows"), model: str | None = None):
        self.flow_dir = Path(flow_dir)
        self.discovery = OpenAIFlowDiscovery(model)
        self.coverage = CoverageCalculator()

    async def run(self, url: str) -> dict:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            structure = await page.locator(
                "a,button,select,input,[role=button]"
            ).evaluate_all(
                "elements => elements.map(element => ({tag: element.tagName, "
                "role: element.getAttribute('role'), text: element.innerText, "
                "id: element.id, className: element.className} ))"
            )
            structure = str(structure)[:20000]
            store = FlowStore(self.flow_dir / f"{urlsplit(url).hostname}.json")
            cached = store.load()
            fingerprint = store.fingerprint(structure)
            flow = cached["flow"] if cached and cached["fingerprint"] == fingerprint else None
            if flow is None:
                flow = self.discovery.discover(url, structure)
                store.save(fingerprint, flow)
            pages = [url, *flow["pages"]]
            pages = list(dict.fromkeys(pages))[:5]
            results = [await self._page(page, flow["languages"], page_url) for page_url in pages]
            await context.close()
            await browser.close()
            return {"url": url, "pages": results, "flow_fingerprint": fingerprint}

    async def _page(self, page, selectors: dict, page_url: str) -> dict:
        result = {"url": page_url, "languages": {}}
        for language in self.LANGUAGES:
            await page.goto(page_url, wait_until="domcontentloaded")
            request_urls = []
            page.on("request", lambda request: request_urls.append(request.url))
            selector = selectors.get(language)
            if selector:
                await page.locator(selector).first.click(timeout=5000)
                await page.wait_for_load_state("networkidle")
            text = await page.locator("body").inner_text()
            result["languages"][language] = {
                "coverage": self.coverage.calculate(text, language).to_dict(),
                "provenance": classify(request_urls, page.url),
            }
        return result
