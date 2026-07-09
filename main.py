import argparse
import csv
import re
import tempfile
import zipfile
from pathlib import Path

import jinja2

FILES_TO_EXTRACT = [
    "Skills.csv",
    "Publications.csv",
    "Profile.csv",
    "Positions.csv",
    "Languages.csv",
    "PhoneNumbers.csv",
    "Email Addresses.csv",
    "Honors.csv",
    "Education.csv",
    "Certifications.csv",
]

PROFILE_FILE = "Profile.csv"
SINGLETON_FILES = {PROFILE_FILE}
LIST_FILES = set(FILES_TO_EXTRACT) - SINGLETON_FILES


def _normalize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()


def parse_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [{_normalize(k): v for k, v in row.items()} for row in reader]


def load_data(extracted: dict[str, Path]) -> dict:
    data = {}
    for logical_name, filepath in extracted.items():
        rows = parse_csv(filepath)
        key = _normalize(logical_name.replace(".csv", ""))

        if logical_name == "PhoneNumbers.csv":
            rows = [r for r in rows if r.get("number", "").strip()]
        elif logical_name == "Email Addresses.csv":
            rows = [r for r in rows if r.get("primary", "").strip().lower() == "yes"]

        if logical_name in SINGLETON_FILES:
            data[key] = rows[0] if rows else {}
        else:
            data[key] = rows
    return data


def render(template_path: Path, data: dict) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path.parent))
    template = env.get_template(template_path.name)
    return template.render(**data)


def validate_zip_path(zip_path: str) -> Path:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        print(f"Error: {zip_path} does not exist")
        return
    if not zip_path.is_file():
        print(f"Error: {zip_path} is not a file")
        return
    if not zip_path.suffix == ".zip":
        print(f"Error: {zip_path} is not a ZIP file")
        return
    return zip_path


def extract_files(zip_path: Path, tmpdir: str) -> dict[str, Path]:
    extracted = {}
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for file in FILES_TO_EXTRACT:
            try:
                zip_ref.extract(file, tmpdir)
                extracted[file] = Path(tmpdir) / file
            except KeyError:
                print(f"Warning: {file} not found in ZIP")
    return extracted


def main(zip_path: str, output_file: str | None = None):
    zip_path = validate_zip_path(zip_path)
    if not zip_path:
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        extracted = extract_files(zip_path, tmpdir)
        data = load_data(extracted)

    output = Path(output_file) if output_file else Path("cv.html")
    html = render(Path("template.html"), data)
    output.write_text(html, encoding="utf-8")
    print(f"CV generated: {output.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Linkedin CV", description="Creates a CV from a LinkedIn ZIP file"
    )
    parser.add_argument("zip_path", help="Path to the LinkedIn ZIP file")
    parser.add_argument(
        "--output_file", help="Path for the generated CV HTML (default: cv.html)"
    )
    args = parser.parse_args()
    main(zip_path=args.zip_path, output_file=args.output_file)
