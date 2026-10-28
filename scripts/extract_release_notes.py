#!/usr/bin/env python3
"""Extract exactly one non-empty version section; never fall back to the whole log."""
import argparse,re
from pathlib import Path

def extract(text,version):
    sections=list(re.finditer(r'^## ([^\n]+)\n',text,re.M))
    matches=[(i,m) for i,m in enumerate(sections) if m.group(1).strip()==version]
    if len(matches)!=1:raise ValueError('Expected exactly one changelog section for version')
    i,m=matches[0];end=sections[i+1].start() if i+1<len(sections) else len(text)
    body=text[m.end():end].strip()
    if not body:raise ValueError('Release notes are empty')
    return body+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('version');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    a.output.write_text(extract((root/'plugins/kai-icloud-calendar/CHANGELOG.md').read_text(),a.version))
