import csv
import json
import os
import requests
# TODO: find a better location for this code

def get_nl_and_en_label(wikidata_identifier, wikidata_endpoint):
    """Gets the NL and EN labels for the identifier
    :param wikidata_identifier the Qname of the identifier
    :param wikidata_endpoint the url of the wikidata endpoint
    :returns the Dutch label and the English label"""
    query = f""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                    PREFIX wd: <http://www.wikidata.org/entity/> 
                    SELECT DISTINCT ?roleLabel
                    WHERE{{ 
                        {{
                            wd:{wikidata_identifier} rdfs:label ?roleLabel .
                            FILTER (langMatches( lang(?roleLabel), "NL" ) )
                        }}
                    UNION
                        {{
                            wd:{wikidata_identifier} rdfs:label ?roleLabel .
                            FILTER (langMatches( lang(?roleLabel), "EN" ) )
                        }}
                    }}"""
    response = requests.get(
                            wikidata_endpoint,
                            params={"query": query},
                            headers = {"Accept": "application/sparql-results+json",
                                    "User-Agent": "wikidataMusicRoleCleaner/0.0 (http://www.beeldengeluid.nl) "})
    nl_label = ""
    en_label = ""
    if response.json()['results']['bindings']:
        for binding in response.json()['results']['bindings']:
            if 'roleLabel' in binding:
                if binding['roleLabel']['xml:lang'] == 'nl':
                    nl_label = binding['roleLabel']['value']
                elif binding['roleLabel']['xml:lang'] == 'en':
                    en_label = binding['roleLabel']['value']
    return nl_label, en_label


if __name__ == "__main__":
    """Main function, reads in files of roles, retrieves NL labels for wikidata concepts
    and creates a lookup with the concept ID and label, and an index for matching"""
    wikidata_endpoint = " https://query.wikidata.org/bigdata/namespace/wdq/sparql"

    cleaned_data = [["Role", "Wikidata identifier", "Wikidata label", "UM identifier", "UM label"]]

    for file in os.listdir("util"):
        if file.endswith(".csv") and file != "music_roles.csv" and file != "music_role_labels.csv":
            print(f"Processing {file}")
            with open(os.sep.join(["util", file]), "r") as f:
                file_reader = csv.reader(f)
                header = True
                for row in file_reader:
                    if header:
                        header = False
                        continue
                    nl_label = ""
                    en_label = ""
                    wikidata_identifier = row[2]
                    um_identifier = row[5] if len(row) > 5 else ""
                    if wikidata_identifier:
                        nl_label, en_label = get_nl_and_en_label(wikidata_identifier, wikidata_endpoint)

                    if wikidata_identifier or um_identifier:  # only write rows with mappings
                        cleaned_row = [
                                        row[0],
                                        f"http://www.wikidata.org/entity/{wikidata_identifier}",
                                        nl_label if nl_label else en_label,
                                        um_identifier,
                                        row[4] if um_identifier else ""
                                        ]
                        cleaned_data.append(cleaned_row)

    with open(os.sep.join(["util", "music_roles.csv"]), "w") as f:
        csv_writer = csv.writer(f)
        for cleaned_row in cleaned_data:
            csv_writer.writerow(cleaned_row)
