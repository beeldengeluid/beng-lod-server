import requests
from typing import List
import json

# from rdflib import Graph
# from rdflib.plugins.stores.sparqlstore import SPARQLStore
# from rdflib.namespace import SDO


# def get_datasets(sparql_endpoint: str) -> List[str]:
#     rdf_store = SPARQLStore(sparql_endpoint, initNs={"sdo": SDO}, returnFormat="json")
#     q = "SELECT ?dataset WHERE { ?s a sdo:DataCatalog . ?s sdo:dataset ?dataset }"
#     qres = rdf_store.query(q)
#     datasets = [row.dataset for row in qres]
#     return datasets


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


def validate_dataset(nde_validate_api: str, dataset_uri: str) -> bool:
    """Use the API to validate the dataset. Once validated it can be POSTED to the API."""
    headers = {
        "Content-type": "application/ld+json",
        "Accept": "application/ld+json",
    }
    data = {"@id": dataset_uri}
    resp = requests.put(nde_validate_api, json=data, headers=headers)
    if resp.status_code == 200:
        # res_dict = json.loads(resp.text)
        # print(json.dumps(res_dict, indent=4))
        return True
    elif resp.status_code == 400:
        print(
            "400: One or more dataset descriptions are invalid according to the Requirements for Datasets. "
            "The response body contains a list of SHACL violations."
        )
        print(resp.text)
    elif resp.status_code == 406:
        print("406: The URL can be resolved but it contains no datasets.")
    elif resp.status_code == 404:
        print("404: The URL cannot be resolved.")
    else:
        print(
            f"NDE dataset register validate api was not successful: {resp.status_code}."
        )
    return False


def register_dataset(nde_register_api: str, dataset_uri: str):
    """Use the NDE Dataset Register API to register the dataset."""
    headers = {
        "Content-type": "application/ld+json",
        "Accept": "application/ld+json",
    }
    data = {"@id": dataset_uri}
    resp = requests.post(nde_register_api, json=data, headers=headers)

    if resp.status_code == 202:
        res_dict = json.loads(resp.text)
        print(json.dumps(res_dict, indent=4))
        return True
    elif resp.status_code == 400:
        print(
            "400: One or more dataset descriptions are invalid according to the Requirements for Datasets. "
            "The response body contains a list of SHACL violations."
        )
        print(resp.text)
    elif resp.status_code == 403:
        print(
            "The submitted URL is not on the domain name allow list. "
            "Contact us to have your intitution’s domain name added."
        )
    elif resp.status_code == 404:
        print("404: The URL cannot be resolved.")
    elif resp.status_code == 406:
        print("406: The URL can be resolved but it contains no datasets.")
    else:
        print(
            f"NDE dataset register validate api was not successful: {resp.status_code}."
        )
    return False


if __name__ == "__main__":
    SPARQL_ENDPOINT = "https://cat.apis.beeldengeluid.nl/sparql"
    api_validate = (
        "https://datasetregister.netwerkdigitaalerfgoed.nl/api/datasets/validate"
    )
    api_register = (
        "https://datasetregister.netwerkdigitaalerfgoed.nl/api/datasets"
    )
    for dataset_uri in get_datasets(SPARQL_ENDPOINT):
        print(f"Validating dataset: {dataset_uri}")
        if validate_dataset(api_validate, dataset_uri) is False:
            continue
        print(f"Registering dataset: {dataset_uri}")
        if register_dataset(api_register, dataset_uri):
            print('Done!')
