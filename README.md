# linkedin-cv

Generates a simple CV from a LinkedIn data export ZIP file.

## How to get data from LinkedIn

1. Go to **Settings & Privacy** → **Data privacy** → **Get a copy of your data**.
2. Select **Download larger data archive...**.
3. Click **Request archive**.
4. LinkedIn will email you a download link to a ZIP file when it's ready.

## How to run

### Using UV

```bash
uv run main.py <path-to-linkedin-zip>
```

### Using pip

```bash
pip install -e .
python3 main.py <path-to-linkedin-zip>
```

## Parameters

| Argument        | Description                                                                 |
| --------------- | --------------------------------------------------------------------------- |
| `zip_path`      | Path to the LinkedIn data export ZIP file (positional, required)            |
| `--output_file` | Path for the generated CV HTML. Default: `cv.html` in the current directory |
