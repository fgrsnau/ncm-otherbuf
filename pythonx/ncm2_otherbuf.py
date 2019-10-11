# -*- coding: utf-8 -*-

import itertools
import re

import vim
from ncm2 import Ncm2Source, getLogger


logger = getLogger(__name__)


class BufferData:

    __slots__ = ('changed', 'words')

    def __init__(self, words=None):
        self.changed = False
        if words is not None:
            self.words = set(words)
        else:
            self.words = set()


class Source(Ncm2Source):

    PATTERN = re.compile(r'\w+')
    WORDS_PER_BUFFER = 1000

    def __init__(self, nvim):
        super().__init__(nvim)
        self.active_bufnr = None
        self.buffers = dict()
        self.update()

    def buffer_is_managed(self, buf):
        return vim.eval('buflisted({})'.format(buf.number))

    def buffer_needs_update(self, buf):
        is_new = not buf.number in self.buffers
        has_changed = not is_new and self.buffers[buf.number].changed
        return is_new or has_changed

    def update(self):
        buffers_present = set()

        for buf in self.nvim.buffers:
            if self.buffer_is_managed(buf):
                if self.buffer_needs_update(buf):
                    self.buffers[buf.number] = self.rescan_buffer(buf)
                buffers_present.add(buf.number)

        self.buffers = {k: v for k, v in self.buffers.items() if k in buffers_present}

    def rescan_buffer(self, buf):
        logger.info('rescan_buffer(%s)', buf.number)

        words = dict()
        def inc_word(word):
            count = words.get(word, 0)
            words[word] = count + 1

        for line in buf:
            for word in self.PATTERN.finditer(line):
                inc_word(word.group())

        sorted_words = sorted(words.items(), reverse=True, key=lambda x: x[1])
        sorted_words = (word for word, count in sorted_words)
        result = BufferData(itertools.islice(sorted_words, self.WORDS_PER_BUFFER))
        logger.info('keyword refresh complete, count: %s', len(result.words))
        return result

    def on_complete(self, ctx):
        base = ctx['base']
        matcher = self.matcher_get(ctx['matcher'])
        matches = []
        for bufnr, buf in self.buffers.items():
            if bufnr != ctx['bufnr']:
                for word in buf.words:
                    item = self.match_formalize(ctx, word)
                    if matcher(base, item):
                        matches.append(item)
        self.complete(ctx, ctx['startccol'], matches)

    def on_warmup(self, ctx):
        bufnr = ctx['bufnr']
        logger.info('warmstarting for buffer %s', bufnr)

        if self.active_bufnr is not None:
            buf = self.buffers.get(self.active_bufnr)
            if buf:
                buf.changed = True
            else:
                logger.debug('did not find last active buffer %s in my buffer list', self.active_bufnr)
        self.active_bufnr = bufnr

        self.update()


source = Source(vim)

on_complete = source.on_complete
on_warmup = source.on_warmup
