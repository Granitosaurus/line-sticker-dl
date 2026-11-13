import asyncio

import pytest
from click.testing import CliRunner

from linestickerdl import cli
from linestickerdl.cli import Runner, main
from linestickerdl.downloader import LineStickerSpider

CDN = 'https://stickershop.line-scdn.net/stickershop/v1/sticker'
STICKERS = [f'{CDN}/2/iPhone/sticker@2x.png', f'{CDN}/1/iPhone/sticker@2x.png']
AUDIO = [f'{CDN}/1/android/sticker_sound.m4a']


@pytest.fixture
def crawled(monkeypatch):
    """Stub out network crawling and record which page ids were requested"""
    requested = []

    async def crawl_pages(self, page_ids):
        requested.extend(page_ids)
        return list(STICKERS), list(AUDIO)

    monkeypatch.setattr(LineStickerSpider, 'crawl_pages', crawl_pages)
    return requested


def test_prints_sorted_sticker_urls(crawled):
    result = CliRunner().invoke(main, ['9044256'])
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == sorted(STICKERS)
    assert crawled == ['9044256']


def test_accepts_store_urls(crawled):
    result = CliRunner().invoke(main, ['https://store.line.me/stickershop/product/9044256/en'])
    assert result.exit_code == 0, result.output
    assert crawled == ['9044256']


def test_audio_flag_includes_sound_files(crawled):
    result = CliRunner().invoke(main, ['1', '--audio'])
    assert result.exit_code == 0, result.output
    assert AUDIO[0] in result.stdout.splitlines()


class FakeProcess:
    def __init__(self, returncode):
        self.returncode = returncode

    async def wait(self):
        return self.returncode


@pytest.fixture
def sticker_files(tmp_path):
    for name in ('1 2.png', '1 2.m4a', '3.png'):
        (tmp_path / name).write_bytes(b'')
    return tmp_path


def test_convert_output_removes_sources_on_success(monkeypatch, sticker_files):
    calls = []

    async def create_subprocess_exec(*args, **kwargs):
        calls.append(args)
        return FakeProcess(0)

    monkeypatch.setattr(cli.asyncio, 'create_subprocess_exec', create_subprocess_exec)
    asyncio.run(Runner.convert_output(None, sticker_files))

    path = sticker_files / '1 2'
    # paths with spaces must be passed as single arguments
    assert calls == [('ffmpeg', '-i', f'{path}.png', '-i', f'{path}.m4a', f'{path}.mp4', '-y')]
    assert sorted(p.name for p in sticker_files.iterdir()) == ['3.png']


def test_convert_output_keeps_sources_on_failure(monkeypatch, sticker_files):
    async def create_subprocess_exec(*args, **kwargs):
        return FakeProcess(1)

    monkeypatch.setattr(cli.asyncio, 'create_subprocess_exec', create_subprocess_exec)
    asyncio.run(Runner.convert_output(None, sticker_files))

    assert sorted(p.name for p in sticker_files.iterdir()) == ['1 2.m4a', '1 2.png', '3.png']
