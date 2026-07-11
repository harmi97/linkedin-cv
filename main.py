import csv
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

import jinja2
import typer

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

TEMPLATES = {"basic": "templates/basic.html"}


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


app = typer.Typer(help="Creates a CV from a LinkedIn ZIP file")


@app.command()
def main(
    zip_path: Annotated[
        str | None, typer.Argument(help="Path to the LinkedIn ZIP file")
    ] = None,
    output_file: Annotated[
        str, typer.Option("--output-file", "-o", help="Path for the generated CV HTML")
    ] = "cv.html",
    test_run: Annotated[
        bool,
        typer.Option("--test-run", help="Run with sample data from samples/input/"),
    ] = False,
    font: Annotated[
        str, typer.Option("--font", help="Font to use for the CV")
    ] = "Calibri",
):
    if not test_run and not zip_path:
        raise typer.BadParameter("zip_path is required when --test-run is not used")

    if test_run:
        samples_dir = Path("samples/input")

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            zip_path_obj = Path(tmp_zip.name)

        try:
            with zipfile.ZipFile(zip_path_obj, "w") as zipf:
                for csv_file in FILES_TO_EXTRACT:
                    csv_path = samples_dir / csv_file
                    if csv_path.exists():
                        zipf.write(csv_path, csv_file)

            with tempfile.TemporaryDirectory() as tmpdir:
                extracted = extract_files(zip_path_obj, tmpdir)
                data = load_data(extracted)
        finally:
            zip_path_obj.unlink(missing_ok=True)

        output = Path("cv.html")
    else:
        zip_path_validated = validate_zip_path(zip_path)
        if not zip_path_validated:
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            extracted = extract_files(zip_path_validated, tmpdir)
            data = load_data(extracted)

        output = Path(output_file)
    data["font"] = f'"{font}"'
    html = render(Path(TEMPLATES["basic"]), data)
    output.write_text(html, encoding="utf-8")
    print(f"CV generated: {output.resolve()}")


if __name__ == "__main__":
    app()
