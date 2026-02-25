#!/usr/bin/env python3
import csv
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def norm_phone(v: str) -> str:
    s = (v or '').strip()
    if not s:
        return ''
    if re.fullmatch(r'\d+\.\d+E\d+', s, flags=re.IGNORECASE):
        try:
            s = format(int(float(s)), 'd')
        except Exception:
            pass
    digits = re.sub(r'\D+', '', s)
    if not digits:
        return ''
    if len(digits) == 10:
        digits = '7' + digits
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    return '+' + digits if len(digits) == 11 else digits


def parse_xlsx(path: str):
    with zipfile.ZipFile(path) as zf:
        shared = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
            for si in root.findall('a:si', NS):
                texts = [t.text or '' for t in si.findall('.//a:t', NS)]
                shared.append(''.join(texts))

        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in zf.namelist():
            raise RuntimeError('sheet1.xml not found')

        sheet = ET.fromstring(zf.read(sheet_path))
        rows = []
        for row in sheet.findall('a:sheetData/a:row', NS):
            vals = []
            for c in row.findall('a:c', NS):
                t = c.attrib.get('t')
                v = c.find('a:v', NS)
                if v is None:
                    vals.append('')
                else:
                    text = v.text or ''
                    if t == 's':
                        try:
                            vals.append(shared[int(text)])
                        except Exception:
                            vals.append(text)
                    else:
                        vals.append(text)
            rows.append(vals)
        return rows


def main():
    if len(sys.argv) < 2:
        print('Usage: xlsx_leads_to_csv.py <xlsx_path> [csv_out] [external_locator] [source_system]', file=sys.stderr)
        sys.exit(1)

    xlsx = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else '-'
    external_locator = sys.argv[3] if len(sys.argv) > 3 else f'local://{xlsx}'
    source_system = sys.argv[4] if len(sys.argv) > 4 else 'manual'

    rows = parse_xlsx(xlsx)
    if not rows:
        print('Empty workbook', file=sys.stderr)
        sys.exit(2)

    header = [h.strip() for h in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    phone_cols = [i for i, name in enumerate(header) if name == 'Телефон']

    def get(r, col, default=''):
        i = idx.get(col)
        if i is None or i >= len(r):
            return default
        return (r[i] or '').strip()

    fieldnames = [
        'client_ref',
        'source_system',
        'external_locator',
        'record_key',
        'tags',
    ]

    fh = sys.stdout if out == '-' else open(out, 'w', newline='', encoding='utf-8')
    try:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row_num, r in enumerate(rows[1:], start=2):
            company = get(r, 'Наименование')
            if not company:
                continue

            phone1 = ''
            phone2 = ''
            if len(phone_cols) >= 1 and phone_cols[0] < len(r):
                phone1 = norm_phone(r[phone_cols[0]])
            if len(phone_cols) >= 2 and phone_cols[1] < len(r):
                phone2 = norm_phone(r[phone_cols[1]])

            city = get(r, 'Город')
            rubric = get(r, 'Рубрики')
            seed = f"{company}|{phone1}|{phone2}|{city}|{row_num}".encode('utf-8')
            client_ref = 'cli_' + hashlib.sha256(seed).hexdigest()[:24]

            tags = '|'.join([x for x in [city, rubric] if x])
            writer.writerow({
                'client_ref': client_ref,
                'source_system': source_system,
                'external_locator': external_locator,
                'record_key': f'row_{row_num}',
                'tags': tags,
            })
    finally:
        if fh is not sys.stdout:
            fh.close()


if __name__ == '__main__':
    main()
