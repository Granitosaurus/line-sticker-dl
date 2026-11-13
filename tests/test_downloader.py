import asyncio
import json
from html import escape

import pytest

from linestickerdl.downloader import LineStickerSpider

CDN = 'https://stickershop.line-scdn.net/stickershop/v1/sticker'


def preview_item(id_, static=True, animation=False, popup=False, sound=False):
    data = {
        'type': 'static',
        'id': id_,
        'staticUrl': f'{CDN}/{id_}/iPhone/sticker@2x.png?v=1' if static else '',
        'animationUrl': f'{CDN}/{id_}/iPhone/sticker_animation@2x.png?v=1' if animation else '',
        'popupUrl': f'{CDN}/{id_}/iPhone/sticker_popup.png?v=1' if popup else '',
    }
    if sound:
        data['soundUrl'] = f'{CDN}/{id_}/android/sticker_sound.m4a?v=1'
    return f'<li class="FnStickerPreviewItem" data-preview="{escape(json.dumps(data))}"></li>'


def page(*items):
    return f'<html><body><ul>{"".join(items)}</ul></body></html>'


class FakeResponse:
    def __init__(self, body=b'', data=None):
        self.body = body
        self.data = data

    async def read(self):
        return self.body

    async def json(self):
        return self.data


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.requested = []

    async def get(self, url):
        self.requested.append(url)
        return self.response

    async def close(self):
        pass


@pytest.fixture
def spider():
    return LineStickerSpider()


def test_parse_page_prefers_popup_then_animation_then_static(spider):
    body = page(
        preview_item('1', static=True),
        preview_item('2', static=True, animation=True),
        preview_item('3', static=True, animation=True, popup=True),
    )
    stickers, audio = spider.parse_page(body)
    assert stickers == [
        f'{CDN}/1/iPhone/sticker@2x.png?v=1',
        f'{CDN}/2/iPhone/sticker_animation@2x.png?v=1',
        f'{CDN}/3/iPhone/sticker_popup.png?v=1',
    ]
    assert audio == []


def test_parse_page_collects_sound(spider):
    body = page(preview_item('1', animation=True, sound=True), preview_item('2'))
    stickers, audio = spider.parse_page(body)
    assert len(stickers) == 2
    assert audio == [f'{CDN}/1/android/sticker_sound.m4a?v=1']


def test_parse_page_without_stickers(spider):
    assert spider.parse_page(page()) == ([], [])


@pytest.mark.parametrize('value, expected', [
    ('https://store.line.me/stickershop/product/9044256/en', ['9044256']),
    ('https://store.line.me/stickershop/product/9044256', ['9044256']),
    ('9044256', []),
])
def test_re_sticker_page_id(value, expected):
    assert LineStickerSpider.re_sticker_page_id.findall(value) == expected


def test_crawl_search_maps_titles_to_ids(spider):
    data = {'items': [{'title': 'Cat', 'id': '1'}, {'title': 'Dog', 'id': '2'}]}
    spider._con = FakeSession(FakeResponse(data=data))
    assert asyncio.run(spider.crawl_search('pets')) == {'Cat': '1', 'Dog': '2'}
    assert 'query=pets' in spider._con.requested[0]


def test_dl_file_names_file_by_sticker_id(spider, tmp_path):
    spider._con = FakeSession(FakeResponse(body=b'sound'))
    asyncio.run(spider.dl_file(f'{CDN}/42/android/sticker_sound.m4a?v=1', tmp_path))
    assert (tmp_path / '42.m4a').read_bytes() == b'sound'


def test_session_is_created_lazily_and_closed():
    async def run():
        spider = LineStickerSpider()
        assert spider._con is None
        session = spider.con
        assert spider.con is session
        await spider.close()
        assert session.closed
        assert spider._con is None

    asyncio.run(run())
