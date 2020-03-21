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
def main(ids_or_urls, output, search, speed):
    """Line sticker downloader cli application"""
    ids = []
    for id_ in ids_or_urls:
        found = LineStickerSpider.re_sticker_page_id.findall(id_)
        ids.append(found[0] if found else id_)
    runner = Runner(speed)
    if search:
        ids = runner.search_stickers(search)
    start = time()
    runner.download_page(ids, output)
    echo(f'finished in: {time() - start:.2f} seconds', err=True)


class Runner:
    """
    runner wrapper for cli commands
    """
    def __init__(self, speed):
        self.speed = speed
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
        # 9044256
        ids = list(ids)
        stickers = self.loop.run_until_complete(self.spider.crawl_pages(ids))
        echo(f'found {len(stickers)} stickers', err=True)
        if not output:
            echo('\n'.join(stickers))
        else:
            output = Path(output)
            output.mkdir(exist_ok=True)
            echo(f'downloading stickers to {output}', err=True)
            self.loop.run_until_complete(self.spider.dl_files(stickers, output=output))


if __name__ == '__main__':
    main()
