import os
import json
import csv
from typing import Any

import requests

COLS_TO_DELETE = [
    "abcd-db",
    "teaching-paradimes",
    "fackel-texte",
    "brenner",
    "jpbriefe",
    "staribacher",
]

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


def _delete_collection(base_url: str, timeout: float, collection_name: str) -> bool:
    response = requests.delete(
        f"{base_url}/collections/{collection_name}",
        headers=_headers(),
        timeout=timeout,
    )
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


def delete_collections(base_url: str, timeout: float) -> None:
    for collection_name in COLS_TO_DELETE:
        try:
            _delete_collection(base_url, timeout, collection_name)
        except requests.RequestException:
            continue


def _format_owners(metadata: Any) -> str:
    if not isinstance(metadata, dict):
        return "not set"

    owners = metadata.get("owners")
    if isinstance(owners, list):
        owner_values = [str(owner).strip() for owner in owners if str(owner).strip()]
        return ", ".join(owner_values) if owner_values else "not set"
    if isinstance(owners, str) and owners.strip():
        return owners.strip()

    return "not set"


def _format_description(metadata: Any) -> str:
    if not isinstance(metadata, dict):
        return "not set"

    description = metadata.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()
    if description is not None and str(description).strip():
        return str(description).strip()

    return "not set"


def _format_service_ids(metadata: Any) -> str:
    if not isinstance(metadata, dict):
        return "not set"

    service_ids = metadata.get("service_ids")
    if isinstance(service_ids, list):
        service_id_values = [
            str(service_id).strip()
            for service_id in service_ids
            if str(service_id).strip()
        ]
        return ", ".join(service_id_values) if service_id_values else "not set"
    if service_ids is not None and str(service_ids).strip():
        return str(service_ids).strip()

    return "not set"


def _has_service_ids(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False

    service_ids = metadata.get("service_ids")
    if isinstance(service_ids, list):
        return any(str(service_id).strip() for service_id in service_ids)
    return bool(str(service_ids).strip()) if service_ids is not None else False


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
    collections_with_metadata = 0

    for collection in collections:
        name = str(collection.get("name", ""))
        num_documents = int(collection.get("num_documents", 0) or 0)
        fields = collection.get("fields", [])
        nr_of_fields = len(fields) if isinstance(fields, list) else 0
        metadata = collection.get("metadata")
        if _has_service_ids(metadata):
            collections_with_metadata += 1
        owners = _format_owners(metadata)
        description = _format_description(metadata)
        service_ids = _format_service_ids(metadata)

        total_documents += num_documents
        collection_stats.append(
            {
                "col_name": name,
                "nr_of_documents": num_documents,
                "nr_of_fields": nr_of_fields,
                "owners": owners,
                "description": description,
                "service_ids": service_ids,
            }
        )

    return {
        "nr_of_collections": len(collection_stats),
        "with_metadata": collections_with_metadata,
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
        writer.writerow(
            [
                "col_name",
                "nr_of_documents",
                "nr_of_fields",
                "owners",
                "description",
                "service_ids",
            ]
        )
        for item in ordered_collections:
            writer.writerow(
                [
                    item.get("col_name", ""),
                    item.get("nr_of_documents", 0),
                    item.get("nr_of_fields", 0),
                    item.get("owners", "not set"),
                    item.get("description", "not set"),
                    item.get("service_ids", "not set"),
                ]
            )


def main() -> None:
    base_url = _build_base_url()
    timeout = _parse_timeout(TYPESENSE_TIMEOUT)
    delete_collections(base_url, timeout)
    stats = build_stats()
    with open("stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)
    write_csv(stats)


if __name__ == "__main__":
    main()
