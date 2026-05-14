import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'packages' / 'shared' / 'openapi' / 'backend.openapi.json'


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    OUTPUT.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote OpenAPI schema to {OUTPUT}')


if __name__ == '__main__':
    main()
