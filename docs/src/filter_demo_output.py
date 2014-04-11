#!/usr/bin/env python
# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import os
import re
import sys

from xml.sax.saxutils import escape

from cStringIO import StringIO

if not os.path.exists('ansi2html'):
  print 'You must run ./make_docs.sh once before running this script.'
  sys.exit(1)

# This dependency is pulled in by make_docs.sh
# if it doesn't exist, run ./make_docs.sh first
sys.path.insert(0, 'ansi2html')

import ansi2html            # pylint: disable=F0401, W0611
import ansi2html.converter  # pylint: disable=F0401, W0611

def simpleXML(string):
  BRIGHT = 1
  DIM    = 2
  NORMAL = 22
  RESET  = 0
  ESC_RE = re.compile('(\x1B\\[[^m]*?)m')

  ret = StringIO()
  boldstate = False

  for tok in ESC_RE.split(string):
    if not tok:
      continue
    if tok[0] == '\x1b':
      codes = map(int, filter(bool, tok[2:].split(';')))
      if not codes:
        codes = [RESET]
      for code in codes:
        # only care about Bright
        if code == BRIGHT and boldstate is False:
          boldstate = True
          ret.write('<emphasis role="strong">')
        elif code in (DIM, NORMAL, RESET) and boldstate:
          boldstate = False
          ret.write('</emphasis>')
    else:
      ret.write(escape(tok))

  if boldstate:
    ret.write('</emphasis>')

  return ret.getvalue()


def main():
  ansi2html.converter.SCHEME['custom'] = (
      "#000000", "#e42e16", "#19c518", "#e7e71c", "#492ee1",
      "#d338d3", "#33d6e5", "#ffffff",
  )

  backend = sys.argv[1]
  output = sys.stdin.read().rstrip()

  callout_re = re.compile('\x1b\[(\d+)c\n')
  callouts = collections.defaultdict(int)
  for i, line in enumerate(output.splitlines(True)):
    m = callout_re.match(line)
    if m:
      callouts[i + int(m.group(1)) - len(callouts)] += 1

  output = callout_re.sub('', output)

  w = sys.stdout.write

  callout_counter = 1
  if backend == 'xhtml11':
    preamble = (
        '</p></div><div class="listingblock"><div class="content"><pre><code>'
    )
    postamble = '</code></pre></div></div><p><div class="paragraph">'
    c = ansi2html.Ansi2HTMLConverter(inline=True, scheme='custom')

    in_code = False
    body = c.convert(output, full=False)
    for i, line in enumerate(body.splitlines()):
      if line.startswith('# '):
        if in_code:
          w(postamble)
          in_code = False
        w(line[1:])
      else:
        if not in_code:
          w(preamble)
          in_code = True
        ext = ''
        for _ in xrange(callouts[i]):
          if not ext:
            ext += '</span>'
          ext += ' <b>&lt;%d&gt;</b>' % callout_counter
          callout_counter += 1
        if ext:
          ext += '<span>'
        w(line + ext + '\n')
    if in_code:
      w(postamble)
  else:
    preamble = '</simpara><literallayout class="monospaced">'
    postamble = '</literallayout><simpara>'

    in_code = False
    body = simpleXML(output)
    for i, line in enumerate(body.splitlines()):
      if line.startswith('# '):
        if in_code:
          w(postamble)
          in_code = False
        w(line[1:])
      else:
        if not in_code:
          w(preamble)
          in_code = True
        ext = ''
        for _ in xrange(callouts[i]):
          ext += '  <emphasis role="strong">(%d)</emphasis>' % callout_counter
          callout_counter += 1
        w(line + ext + '\n')
    if in_code:
      w(postamble)


if __name__ == '__main__':
  main()