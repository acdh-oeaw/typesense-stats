# typesense-stats

Generate summary statistics for a Typesense instance and export them to `stats.json` and `stats.csv`.

## What it does

The script in `main.py`:

- Connects to the Typesense `/collections` endpoint.
- Collects basic stats for each collection.
- Reads collection metadata when available.
- Writes the results to `stats.json` and `stats.csv`.
- Tries to delete the collections listed in `COLS_TO_DELETE` before collecting stats.

## Requirements

- Python 3.14 or newer
- Access to a running Typesense instance

## Configuration

The script reads these environment variables:

- `TYPESENSE_API_KEY` - API key for Typesense, defaults to `xyz`
- `TYPESENSE_HOST` - Typesense host, defaults to `localhost`
- `TYPESENSE_PORT` - Typesense port, defaults to `8108`
- `TYPESENSE_PROTOCOL` - `http` or `https`, defaults to `http`
- `TYPESENSE_TIMEOUT` - request timeout in seconds, defaults to `120`

## Usage

Run the script with `uv`:

```bash
uv run main.py
```

This creates or updates:

- `stats.json`
- `stats.csv`

## Output

The JSON output includes:

- `nr_of_collections`
- `with_metadata`
- `nr_of_documents`
- `collections`

The CSV output includes these columns:

- `col_name`
- `nr_of_documents`
- `nr_of_fields`
- `owners`
- `description`
- `service_ids`

Missing metadata values are written as `not set`.
