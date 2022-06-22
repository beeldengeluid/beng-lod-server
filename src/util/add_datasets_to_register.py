import requests
from config.settings import Config
from typing import List
import json


def get_datasets(sparql_endpoint: str) -> List[str]:
    """Given a sparql endpoint, get the data catalog and generate an URL list of datasets."""
    query = "SELECT ?dataset WHERE { ?s a sdo:DataCatalog . ?s sdo:dataset ?dataset }"
    datasets = [
        item.get("dataset", {}).get("value")
        for item in sparql_select_query(sparql_endpoint, query)
        if item.get("dataset", {}).get("value")
    ]
    return datasets


def sparql_select_query(sparql_endpoint: str, query: str):
    """Sends a SPARQL SELECT query to the SPARQL endpoint and returns the SPARQL result."""
    params = {"format": "application/sparql-results+json", "query": query}
    resp = requests.get(sparql_endpoint, params=params)
    if resp.status_code == 200:
        res_dict = json.loads(resp.text)
        if res_dict.get("results") and res_dict.get("results").get("bindings"):
            return res_dict["results"]["bindings"]


def validate_dataset(nde_validate_api: str, dataset_uri: str):
    """Use the API to valildate the dataset. Once validated it can be POSTED to the API."""
    try:
        headers = {
            "Content-type": "application/ld+json",
            "Accept": "application/ld+json",
        }
        data = {"@id": dataset_uri}
        resp = requests.put(nde_validate_api, json=data, headers=headers)
        if resp.status_code == 200:
            res_dict = json.loads(resp.text)
            print(json.dumps(res_dict, indent=4))
        elif resp.status_code == 400:
            print(
                "400: One or more dataset descriptions are invalid according to the Requirements for Datasets. "
                "The response body contains a list of SHACL violations."
            )
        elif resp.status_code == 406:
            print("406: The URL can be resolved but it contains no datasets.")
        elif resp.status_code == 404:
            print("404: The URL cannot be resolved.")
        else:
            print(
                f"NDE dataset register validate api was not successful: {resp.status_code}."
            )
    except ConnectionError as e:
        print(str(e))


def register_dataset(nde_register_api: str, dataset_uri: str):
    """Use the NDE Dataset Register API to register the dataset."""
    raise NotImplementedError()


if __name__ == "__main__":
    api_validate = (
        "https://datasetregister.netwerkdigitaalerfgoed.nl/api/datasets/validate"
    )

    # nde_dataset = "https://demo.netwerkdigitaalerfgoed.nl/datasets/kb/2.html"
    # validate_dataset(api_validate, nde_dataset)

    for dataset_uri in get_datasets(Config.SPARQL_ENDPOINT):
        print(f"Validating dataset: {dataset_uri}")
        validate_dataset(api_validate, dataset_uri)
        break
