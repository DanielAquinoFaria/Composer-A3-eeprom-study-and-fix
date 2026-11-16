"""Verify the delivery manifest without dependencies or serial/hardware access."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'MANIFESTO_SHA256.json').read_text(encoding='utf-8'))
    errors = []
    total = 0
    for item in manifest['arquivos']:
        path = (ROOT / item['arquivo']).resolve()
        if not path.is_relative_to(ROOT):
            errors.append('Caminho fora do pacote: ' + item['arquivo'])
            continue
        if not path.is_file():
            errors.append('Ausente: ' + item['arquivo'])
            continue
        data = path.read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            errors.append('Divergente: ' + item['arquivo'])
        total += len(data)
    for error in errors:
        print(error)
    if errors:
        print(f'FALHA: {len(errors)} arquivo(s) ausente(s), divergente(s) ou invalido(s).')
        return 1
    print(f'OK: {len(manifest["arquivos"])} arquivos; {total} bytes conferidos.')
    print('Manifesto local; nao comprova autenticidade nem leitura fisica da EEPROM.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
