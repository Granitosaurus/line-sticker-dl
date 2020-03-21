import asyncio
import json
import os
import re
from asyncio import gather
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

from parsel import Selector
from aiohttp.connector import TCPConnector
from aiohttp.client import ClientSession


class LineStickerSpider:
    # default headers for requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
    }
    # url templates
    urlf_page = 'https://store.line.me/stickershop/product/{id}/en'.format
    urlf_search = 'https://store.line.me/api/search/sticker' \
                  '?query={query}&offset=0&limit=36&type=ALL&includeFacets=false'.format
    # sticker resolve order
    sticker_order = ['sound', 'popup', 'animation', 'static']
    re_sticker_id = re.compile('sticker/([^/]+)')  # sticker id in url
    re_sticker_page_id = re.compile('stickershop/product/([^/]+)')  # sticker shop id in url

    def __init__(self, connection_limit=10):
        connector = TCPConnector(limit=connection_limit)
        self.con = ClientSession(connector=connector, headers=self.headers)

    def __del__(self):
        asyncio.ensure_future(self.con.close())

    async def crawl_search(self, query) -> Dict[str, str]:
        """
        Crawls search and returns title-to-id dictionary, e.g.:
        {"cool sticker #1": '1234233', ...}
        """

        url = self.urlf_search(query=query)
        response = await self.con.get(url)
        data = await response.json()
        results = {}
        for d in data['items']:
            results[d['title']] = d['id']
        return results

    async def crawl_pages(self, page_ids: List[str]) -> List[str]:
        """Crawl sticker pages for sticker urls"""
        all_results = await gather(*[self.crawl_page(id_) for id_ in page_ids])
        return [r for results in all_results for r in results]

    async def crawl_page(self, page_id):
        """crawl single sticker page and parse out sticker file urls"""
        response = await self.con.get(self.urlf_page(id=page_id))
        return self.parse_page(await response.text())

    async def dl_files(self, urls: List[str], output: Path) -> None:
        """Download files from urls asynchroniously"""
        return await gather(*[self.dl_file(url, output) for url in urls])

    async def dl_file(self, url: str, output: Path) -> None:
        """Donwload file and save it to output"""
        id_ = self.re_sticker_id.findall(url)[0]
        response = await self.con.get(url)
        ext = os.path.splitext(urlparse(url).path)[1]
        with open(output / f'{id_}{ext}', 'wb') as f:
            f.write(await response.read())

    def parse_page(self, body: str) -> List[str]:
        """Parse page for sticker urls"""
        sel = Selector(text=body)
        data = sel.css('.FnStickerPreviewItem::attr(data-preview)').extract()
        data = [json.loads(d) for d in data]
        stickers = []
        for d in data:
            for key in self.sticker_order:
                value = d.get(f'{key}Url')
                if value:
                    stickers.append(value)
                    break
        return stickers
