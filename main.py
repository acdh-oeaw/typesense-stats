import os
import json
import csv
from typing import Any

import requests

TYPESENSE_API_KEY = os.environ.get("TYPESENSE_API_KEY", "xyz")
TYPESENSE_TIMEOUT = os.environ.get("TYPESENSE_TIMEOUT", "120")
TYPESENSE_HOST = os.environ.get("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT = os.environ.get("TYPESENSE_PORT", "8108")
TYPESENSE_PROTOCOL = os.environ.get("TYPESENSE_PROTOCOL", "http")


def _build_base_url() -> str:
	return f"{TYPESENSE_PROTOCOL}://{TYPESENSE_HOST}:{TYPESENSE_PORT}"


def _parse_timeout(timeout_value: str) -> float:
	try:
		return float(timeout_value)
	except ValueError:
		return 120.0


def _headers() -> dict[str, str]:
	return {
		"X-TYPESENSE-API-KEY": TYPESENSE_API_KEY,
		"Content-Type": "application/json",
	}


def _get_collections(base_url: str, timeout: float) -> list[dict[str, Any]]:
	response = requests.get(
		f"{base_url}/collections",
		headers=_headers(),
		timeout=timeout,
	)
	response.raise_for_status()
	data = response.json()
	if not isinstance(data, list):
		raise ValueError("Unexpected response from Typesense /collections endpoint")
	return data


def build_stats() -> dict[str, Any]:
	base_url = _build_base_url()
	timeout = _parse_timeout(TYPESENSE_TIMEOUT)
	collections = _get_collections(base_url, timeout)

	collection_stats: list[dict[str, Any]] = []
	total_documents = 0

	for collection in collections:
		name = str(collection.get("name", ""))
		num_documents = int(collection.get("num_documents", 0) or 0)
		fields = collection.get("fields", [])
		nr_of_fields = len(fields) if isinstance(fields, list) else 0

		total_documents += num_documents
		collection_stats.append(
			{
				"col_name": name,
				"nr_of_documents": num_documents,
				"nr_of_fields": nr_of_fields,
			}
		)

	return {
		"nr_of_collections": len(collection_stats),
		"nr_of_documents": total_documents,
		"collections": collection_stats,
	}


def write_csv(stats: dict[str, Any]) -> None:
	ordered_collections = sorted(
		stats.get("collections", []),
		key=lambda item: int(item.get("nr_of_documents", 0) or 0),
		reverse=True,
	)

	with open("stats.csv", "w", encoding="utf-8", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["col_name", "nr_of_documents", "nr_of_fileds"])
		for item in ordered_collections:
			writer.writerow(
				[
					item.get("col_name", ""),
					item.get("nr_of_documents", 0),
					item.get("nr_of_fields", 0),
				]
			)


def main() -> None:
	stats = build_stats()
	with open("stats.json", "w", encoding="utf-8") as f:
		json.dump(stats, f, indent=4)
	write_csv(stats)


if __name__ == "__main__":
	main()
