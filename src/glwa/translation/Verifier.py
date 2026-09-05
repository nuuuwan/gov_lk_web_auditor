from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from .Availability import check
from .Coverage import CoverageCalculator
from .FlowStore import FlowStore
from .OpenAIFlowDiscovery import OpenAIFlowDiscovery
from .Provenance import classify


class TranslationVerifier:
    LANGUAGES = ("en", "si", "ta")

    def __init__(self, flow_dir: Path = Path("translation_mappings"), model: str | None = None):
        self.flow_dir = Path(flow_dir)
        self.discovery = OpenAIFlowDiscovery(model)
        self.coverage = CoverageCalculator()

    async def run(
        self,
        url: str,
        mapping_path: Path | None = None,
        replay: bool = False,
        rediscover: bool = False,
    ) -> dict:
        from playwright.async_api import Error, async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            try:
                response = await page.goto(url, wait_until="domcontentloaded")
            except Error as error:
                await context.close()
                await browser.close()
                return {
                    "url": url,
                    "status": "unavailable",
                    "reason": f"browser navigation failed: {error}",
                    "pages": [],
                }
            visible_text = await page.locator("body").inner_text()
            unavailable = check(
                response.status if response else None,
                page.url,
                visible_text,
                self._redirect_chain(response),
            )
            if unavailable:
                await context.close()
                await browser.close()
                return {"url": url, **unavailable, "pages": []}
            structure = await page.locator(
                "a,button,select,input,[role=button]"
            ).evaluate_all(
                "elements => elements.map(element => ({tag: element.tagName, "
                "role: element.getAttribute('role'), text: element.innerText, "
                "id: element.id, className: element.className} ))"
            )
            structure = str(structure)[:20000]
            store = FlowStore(
                mapping_path or self.flow_dir / f"{urlsplit(url).hostname}.json"
            )
            cached = store.load()
            fingerprint = store.fingerprint(structure)
            if rediscover and not replay:
                cached = None
            if cached and cached["fingerprint"] != fingerprint:
                if replay:
                    raise ValueError("translation mapping is stale for the live page")
                cached = None
            flow = self._flow(cached) if cached else None
            if flow is None or not await self._valid_flow(page, flow):
                if replay:
                    raise ValueError("translation mapping selectors do not match the live page")
                flow = self.discovery.discover(url, structure)
                if not await self._valid_flow(page, flow):
                    raise ValueError("OpenAI flow selectors did not match the live page")
                flow = {**flow, "pages": [url, *flow["pages"]]}
                flow = await self._record_actions(page, flow)
                store.save(fingerprint, flow, url, page.url)
            pages = list(dict.fromkeys(flow["pages"]))[:5]
            results = [await self._page(page, flow, page_url) for page_url in pages]
            await context.close()
            await browser.close()
            return {
                "url": url,
                "pages": results,
                "flow_fingerprint": fingerprint,
                "redirect_chain": self._redirect_chain(response),
            }

    def _flow(self, mapping: dict | None) -> dict | None:
        if not mapping:
            return None
        if "actions" in mapping:
            return {
                "pages": [item["url"] for item in mapping.get("pages", [])],
                "languages": {
                    language: action["locator"]
                    for language, action in mapping["actions"].items()
                    if action.get("kind") == "locator"
                },
                "action_metadata": {
                    language: {
                        key: value
                        for key, value in action.items()
                        if key not in {"kind", "locator"}
                    }
                    for language, action in mapping["actions"].items()
                },
            }
        return mapping.get("flow")

    def _redirect_chain(self, response) -> list[str]:
        if not response:
            return []
        chain = []
        request = response.request
        while request:
            chain.append(request.url)
            request = request.redirected_from
        return list(reversed(chain))

    async def _valid_flow(self, page, flow: dict) -> bool:
        for selector in flow.get("languages", {}).values():
            try:
                if await page.locator(selector).count() == 0:
                    return False
            except Exception:
                return False
        return all(language in flow.get("languages", {}) for language in self.LANGUAGES)

    async def _record_actions(self, page, flow: dict) -> dict:
        metadata = {}
        for language, selector in flow["languages"].items():
            await page.goto(flow["pages"][0], wait_until="domcontentloaded")
            await self._activate(page, selector)
            await page.wait_for_timeout(1500)
            metadata[language] = {
                "resolved_url": page.url,
                "resolved_path": urlsplit(page.url).path,
            }
        return {**flow, "action_metadata": metadata}

    async def _page(self, page, flow: dict, page_url: str) -> dict:
        result = {"url": page_url, "languages": {}}
        for language in self.LANGUAGES:
            await page.goto(page_url, wait_until="domcontentloaded")
            request_urls = []
            page.on("request", lambda request: request_urls.append(request.url))
            selector = flow["languages"].get(language)
            if selector:
                await self._activate(page, selector)
                await page.wait_for_timeout(1500)
            text = await page.locator("body").inner_text()
            result["languages"][language] = {
                "coverage": self.coverage.calculate(text, language).to_dict(),
                "provenance": classify(request_urls, page.url),
                "resolved_url": page.url,
                "resolved_path": urlsplit(page.url).path,
            }
        return result

    async def _activate(self, page, selector: str) -> None:
        control = page.locator(selector).first
        if await control.evaluate("element => element.tagName") == "OPTION":
            select = control.locator("..")
            await select.select_option(value=await control.get_attribute("value"))
            return
        await control.click(timeout=5000)
