#!/usr/bin/env python3
#
# Unown is an EPUB generation utility conforming to EPUB 3.0.
# Copyright (C) 2018 Kiyoshi Aman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program. If not, see
# <https://www.gnu.org/licenses/>.

import sys
import uuid

import os.path as op

import unown

def generate_epub(cfg, uuid, files, filename, mode='all'):
    if mode not in ['white', 'black', 'all']:
        raise ValueError('unknown mode')

    path = op.join('.', cfg['directory'])

    print('Generating {}...'.format(filename))
    if 'single_file' in cfg.keys() and cfg['single_file']:
        print('  Building EPUB Package Document...')
        unown.build_package_singleton(cfg, path, mode)
        print('  Building EPUB Container...')
        unown.make_zip_singleton(filename, path, cfg['source'], filename, mode)
    else:
        print('  Building EPUB Package Document...')
        unown.build_package(cfg, path, files, mode, uuid)
        print('  Building EPUB Container...')
        unown.make_zip(filename, path, files, mode)

def process_list(cfg, mode='white'):
    if mode not in ['white', 'black']:
        raise ValueError('unknown mode')

    listtype = mode + 'list'
    sets = [item for item in cfg[listtype].keys() if not item.endswith('_uuid')]
    count = len(sets)

    print('Processing {}{}...'.format(listtype, 's' if count > 1 else ''))
    for name in sets:
        files = cfg[listtype][name]
        filename = '{} {}.epub'.format(cfg['title'], name)
        uuid_field = '{}_uuid'.format(name)

        if uuid_field not in cfg[listtype]:
            cfg[listtype][uuid_field] = str(uuid.uuid1())

        generate_epub(cfg, cfg[listtype][uuid_field], files, filename, mode)

print('Loading configuration...')
cfg = unown.load_config(sys.argv[1])

if 'whitelist' in cfg.keys():
    filtered = True
    process_list(cfg, 'white')
if 'blacklist' in cfg.keys():
    filtered = True
    process_list(cfg, 'black')
if cfg['generate_all'] or not filtered:
    generate_epub(cfg, cfg['uuid'], None, '{}.epub'.format(cfg['title']), 'all')

print('Saving configuration...')
unown.save_config(sys.argv[1], cfg)
