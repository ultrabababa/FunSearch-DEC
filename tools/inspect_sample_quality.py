import argparse
import csv
from pathlib import Path


def inspect(raw_samples_dir: Path, csv_path: Path) -> None:
    manifest_count = len(list(raw_samples_dir.glob('sample_*_manifest.json')))
    raw_count = len(list(raw_samples_dir.glob('sample_*_*_raw.txt')))
    trimmed_count = len(list(raw_samples_dir.glob('sample_*_*_trimmed.txt')))

    rows = []
    if csv_path.exists():
        with csv_path.open('r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

    thinking_raw = 0
    thinking_trimmed = 0
    empty_trimmed = 0
    for path in raw_samples_dir.glob('sample_*_*_raw.txt'):
        text = path.read_text(encoding='utf-8', errors='ignore')
        if 'thinking process' in text.lower():
            thinking_raw += 1
    for path in raw_samples_dir.glob('sample_*_*_trimmed.txt'):
        text = path.read_text(encoding='utf-8', errors='ignore')
        low = text.lower()
        if 'thinking process' in low:
            thinking_trimmed += 1
        if not text.strip():
            empty_trimmed += 1

    print(f'manifests={manifest_count}')
    print(f'raw_files={raw_count}')
    print(f'trimmed_files={trimmed_count}')
    print(f'csv_rows={len(rows)}')
    print(f'raw_with_thinking={thinking_raw}')
    print(f'trimmed_with_thinking={thinking_trimmed}')
    print(f'trimmed_empty={empty_trimmed}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Inspect sample quality for FunSearch logs')
    parser.add_argument('--raw-samples-dir', default='logs/funsearch_llm_api/raw_samples')
    parser.add_argument('--csv', default='logs/funsearch_llm_api/merged_samples.csv')
    args = parser.parse_args()
    inspect(Path(args.raw_samples_dir), Path(args.csv))


if __name__ == '__main__':
    main()
