"""Извлечь читаемый текст из .doc (OLE) в reports/vkr/data."""
import re
import sys
from pathlib import Path

import olefile

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'reports' / 'vkr' / 'data'
CYRILLIC_RUN = re.compile(r'[\u0400-\u04FF][\u0400-\u04FF0-9\s\.,\-\(\):;№"/]{4,}')


def extract_from_stream(data: bytes) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for encoding in ('utf-16-le', 'cp1251'):
        text = data.decode(encoding, errors='ignore')
        for match in CYRILLIC_RUN.finditer(text):
            line = ' '.join(match.group().split())
            if line in seen or len(line) < 8:
                continue
            seen.add(line)
            lines.append(line)
    return lines


def main():
    docs = list(DATA.glob('*.doc'))
    if not docs:
        print('No .doc files found', file=sys.stderr)
        sys.exit(1)
    path = docs[0]
    ole = olefile.OleFileIO(path)
    all_lines: list[str] = []
    for stream_name in ('WordDocument', '1Table', 'Data'):
        if ole.exists(stream_name):
            all_lines.extend(extract_from_stream(ole.openstream(stream_name).read()))
    ole.close()

    seen: set[str] = set()
    unique: list[str] = []
    for line in all_lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)

    out = ROOT / '_contract_text.txt'
    out.write_text('\n'.join(unique), encoding='utf-8')
    print(f'Extracted {len(unique)} lines from {path.name}')
    for line in unique:
        print(line)


if __name__ == '__main__':
    main()
