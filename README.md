# line-sticker-dl

Command Line Downloader for stickers of popular messaging application [LINE].

e.g. 
https://store.line.me/stickershop/product/9044256/en


# Usage

```shell
Usage: line-sticker-dl [OPTIONS] [IDS_OR_URLS]...

  Line sticker downloader cli application

Options:
  -o, --output DIRECTORY  save sticker files to directory
  -s, --search TEXT       search_stickers for stickers by a query
  -x, --speed INTEGER     concurrent request limit, higher speeds might cause
                          bans  [default: 10]

  -a, --audio             include .m4a audio files for sound stickers
  --mp4                   for sound sticker convert png + m4a into single mp4
                          [requires ffmpeg]

  --help                  Show this message and exit.
```

![demo](demo.svg)

The application can either download straight from urls or shop ids:

```
https://store.line.me/stickershop/product/9044256/en
# shop id in this case being:
9044256
```

or can search sticker shop via query:

```shell
$ line-sticker-dl --search bugcat                                                                                     
? Select stickers:  (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)                         
 » ○ BugCat-Capoo Cute and useful
   ○ BugCat Capoo & Tutu - move move
   ○ Bugcat-Capoo is on the Move! Vol. 2
   ○ BugCat Capoo & Tutu-love and eat
   ○ BugCat-Capoo
```

Output urls to stdout or if `-o`/`--output` flag is given download sticker files to given directory.


# Install

Can be installed via pip:

```shell
$ pip install --user line-sticker-dl
```

or built from source:

```shell script
$ git clone https://github.com/Granitosaurus/line-sticker-dl
$ cd line-sticker-dl
$ pip install .
```

[LINE]: https://store.line.me
