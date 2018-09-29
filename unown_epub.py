#!/usr/bin/env python3

import os
import zipfile
import uuid
import datetime

import os.path as op

from dataclasses import dataclass, field
from typing import List

import jinja2
import tomlkit as toml

env = jinja2.Environment(loader=jinja2.PackageLoader('unown', 'templates'))

mime = {
    'html': 'application/xhtml+xml',
    'xhtml': 'application/xhtml+xml',
    'png':  'image/png',
    'jpg':  'image/jpeg',
    'css':  'text/css',
    'xml':  'application/xml'
}

@dataclass
class File:
    path: str
    name: str
    nav: bool = None

    @property
    def xname(self):
        name, ext = op.splitext(self.name)
        return name + '.xhtml'

    @property
    def samedir(self):
        path = op.split(self.name)[-1]
        name, ext = op.splitext(path)
        return name + '.xhtml'

    @property
    def mime(self):
        name, ext = op.splitext(self.name)
        return mime[ext[1:]]

    @property
    def readable(self):
        return self.name.endswith('.html')

    @property
    def id(self):
        path = 'post' + op.split(self.name)[-1]
        name, ext = op.splitext(path)
        return name

    @property
    def title(self):
        path = 'Post ' + op.split(self.name)[-1]
        name, ext = op.splitext(path)
        return name

@dataclass
class Book:
    title: str
    language: str
    copyright: int
    creator: str
    uuid: str
    subtitle: str = None
    generated: str = None
    contributors: List[str] = field(default_factory=list)
    items: List[File] = field(default_factory=list)

def load_config(filename):
    with open(filename, mode='r') as f:
        cfg = toml.loads(f.read())

    # EPUB requires a unique identifier, and since we're not published yet,
    # a UUID will have to do.
    if 'uuid' not in cfg:
        cfg['uuid'] = str(uuid.uuid1())

    return cfg

def save_config(filename, cfg):
    with open(filename, mode='w') as f:
        f.write(toml.dumps(cfg))

def generate_filelist(path, metadata=False):
    files = []
    oebps_present = False
    meta_present = False

    with os.scandir(path) as d:
        for entry in d:
            if entry.is_dir():
                if entry.name == 'OEBPS':
                    oebps_present = True
                elif entry.name == 'META-INF':
                    meta_present = True
                continue

            files.append(File(path, entry.name))

    if oebps_present:
        with os.scandir(op.join(path, 'OEBPS')) as d:
            for entry in d:
                if entry.is_dir():
                    continue
                files.append(File(path, op.join('OEBPS', entry.name)))

    if meta_present and metadata:
        with os.scandir(op.join(path, 'META-INF')) as d:
            for entry in d:
                if entry.is_dir():
                    continue
                files.append(File(path, op.join('META-INF', entry.name)))

    return files

def build_package(cfg, path):
    package = op.join(path, cfg['directory'], 'epub.opf')
    toc = op.join(path, cfg['directory'], 'OEBPS', 'nav.xhtml')
    book = Book(
        title=cfg['title'],
        subtitle=cfg['subtitle'],
        language=cfg['language'],
        copyright=cfg['copyright'],
        creator=cfg['creator'],
        contributors=cfg['contributors'],
        uuid=cfg['uuid'],
        generated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    if not op.exists(op.join(path, cfg['directory'], 'META-INF')):
        os.mkdir(op.join(path, cfg['directory'], 'META-INF'))

    if op.exists(package):
        os.unlink(package)
    if op.exists(toc):
        os.unlink(toc)

    files = generate_filelist(op.join(path, cfg['directory']))
    book.items = files

    with open(op.join(path, cfg['directory'], 'OEBPS', 'nav.xhtml'), mode='w') as f:
        f.write(env.get_template('nav.html').render(package=book))

    files.append(File(op.join(path, cfg['directory']), 'OEBPS/nav.xhtml', nav=True))

    with open(package, mode='w') as f:
        f.write(env.get_template('package.xml').render(package=book))

def make_zip(filename, filelist):
    doc = zipfile.ZipFile(
        filename,
        mode='x',
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9
    )
    doc.writestr('mimetype', 'application/epub+zip')
    doc.write('templates/container.xml', 'META-INF/container.xml', compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    for file in filelist:
        if file.name.endswith('.png') or file.name.endswith('.jpg'):
            compress = zipfile.ZIP_STORED
        else:
            compress = zipfile.ZIP_DEFLATED

        name = file.xname if file.name.endswith('.html') else file.name

        doc.write(op.join(file.path, file.name), name, compress_type=compress, compresslevel=9)

if __name__ == '__main__':
    import sys

    print('Loading configuration...')
    cfg = load_config(sys.argv[1])
    print('Building EPUB Package Document for {}...'.format(cfg['title']))
    build_package(cfg, '.')
    print('Building EPUB Container...')
    make_zip(sys.argv[2], generate_filelist(op.join('.', cfg['directory']), metadata=True))
    print('Saving configuration...')
    save_config(sys.argv[1], cfg)
