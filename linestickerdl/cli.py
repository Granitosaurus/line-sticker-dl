import os
from pathlib import Path
from time import time

import questionary
from click import echo
import click
import asyncio

from linestickerdl.downloader import LineStickerSpider


@click.command()
@click.argument('ids_or_urls', nargs=-1)
@click.option(
    '-o', '--output',
    help='save sticker files to directory',
    type=click.Path(writable=True, file_okay=False, resolve_path=True)
)
@click.option('-s', '--search', 'search', help='search_stickers for stickers by a query')
@click.option(
    '--speed',
    '-x',
    help='concurrent request limit, higher speeds might cause bans', default=10,
    show_default=True
)
@click.option(
    '--audio',
    '-a',
    help='include .m4a audio files for sound stickers',
    is_flag=True
)
@click.option(
    '--mp4',
    help='for sound sticker convert png + m4a into single mp4 [requires ffmpeg]',
    is_flag=True
)
def main(ids_or_urls, output, search, speed, audio, mp4):
    """Line sticker downloader cli application"""
    if mp4:
        audio = True
    ids = []
    for id_ in ids_or_urls:
        found = LineStickerSpider.re_sticker_page_id.findall(id_)
        ids.append(found[0] if found else id_)
    runner = Runner(speed, audio, mp4)
    if search:
        ids = runner.search_stickers(search)
    start = time()
    runner.download_page(ids, output)
    echo(f'finished in: {time() - start:.2f} seconds', err=True)


class Runner:
    """
    runner wrapper for cli commands
    """

    def __init__(self, speed: int, include_audio: bool, mp4: bool):
        self.speed = speed
        self.include_audio = include_audio
        self.mp4 = mp4
        self.loop = asyncio.get_event_loop()
        self.spider = LineStickerSpider(connection_limit=speed)

    def search_stickers(self, query):
        sticker_pages = self.loop.run_until_complete(self.spider.crawl_search(query))
        selections = questionary.checkbox(
            'Select stickers:',
            choices=list(sticker_pages)).ask()
        ids = [sticker_pages[s] for s in selections]
        return ids

    def download_page(self, ids, output):
        ids = list(ids)
        stickers, audio = self.loop.run_until_complete(self.spider.crawl_pages(ids))
        echo(f'found {len(stickers)} stickers and {len(audio)} files', err=True)
        to_dl = stickers
        if self.include_audio:
            to_dl += audio
        to_dl = sorted(to_dl, key=lambda v: LineStickerSpider.re_sticker_id.findall(v)[0])
        if not output:
            echo('\n'.join(to_dl))
            return
        output = Path(output)
        output.mkdir(exist_ok=True)
        echo(f'downloading stickers to {output}', err=True)
        self.loop.run_until_complete(self.spider.dl_files(to_dl, output=output))
        if self.mp4:
            self.loop.run_until_complete(self.convert_output(output))

    async def convert_output(self, output: Path):
        echo(f'converting png+m4a to mp4', err=True)
        count = 0
        for file in os.listdir(output):
            name, ext = os.path.splitext(file)
            path = output / name
            if ext != '.m4a':
                continue
            # TODO maybe gather this up but it's so quick as it is
            result = await asyncio.create_subprocess_shell(
                f'ffmpeg -i {path}.png -i {path}.m4a {path}.mp4 -y',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            if result.returncode == 0:
                echo(f'  failed to convert {path} png+m4a to mp4', err=True)
            os.remove(f'{path}.png')
            os.remove(f'{path}.m4a')
            count += 1
        echo(f'converted {count} files', err=True)


if __name__ == '__main__':
    main()
