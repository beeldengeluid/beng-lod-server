import csv
import requests

from base_util import relative_from_repo_root


def get_role_for_instrument(instrument):
    """Given the Wikidata identifier for an instrument, searches for a role belonging
    to that instrument. E.g. Guitar -> Guitarist
    :param instrument - the wikidata identifier of the instrument
    :returns the wikidata identifier of the role, if found, otherwise an empty string"""


if __name__ == "__main__":
    """Main function, reads in a file of instrument identifiers and retrieves the roles"""

    roles_to_exclude = ["http://www.wikidata.org/entity/Q1278335",  # instrumentalist
                        "http://www.wikidata.org/entity/Q24229398", # agent
                        "http://www.wikidata.org/entity/Q5", # mens
                        ]
    wikidata_endpoint = " https://query.wikidata.org/bigdata/namespace/wdq/sparql"

    converted_data = [["Role", "Wikidata identifier", "Wikidata label"]]

    # read file
    with open(relative_from_repo_root("resource/instrument_roles.csv"), "r") as f:
        file_reader = csv.reader(f)
        header = True
        for row in file_reader:

            if header:
                header = False
                continue

            wikidata_identifier = row[2]
            print(wikidata_identifier)
            new_role = None
            new_role_label = None
            if wikidata_identifier:

                query = f""" SELECT ?role ?roleLabel
                                WHERE{{ wd:{wikidata_identifier} wdt:P279*/wdt:P1535 ?role .
                                SERVICE wikibase:label {{bd:serviceParam wikibase:language "nl"}}
                                }}"""
                response = requests.get(
                                        wikidata_endpoint,
                                        params={"query": query},
                                        headers = {"Accept": "application/sparql-results+json",
                                                "User-Agent": "wikidataMusicRoleRetriever/0.0 (http://www.beeldengeluid.nl) "})
                
                if response.json()['results']['bindings']:
                    for binding in response.json()['results']['bindings']:
                        new_role = binding['role']['value']

                        if new_role not in roles_to_exclude:  # take the first role that is specific 
                            new_role_label = binding['roleLabel']['value']

                            if new_role_label == new_role.split("/")[-1]:  # if label is the identifier, no Dutch label available
                                new_role_label = "No Dutch label"  # 
                            print(f"Role for {row[0]} is {new_role}, {new_role_label}")
                            break
                        else:
                            new_role = None  # discard the role, as we don't want it
                    if not new_role:  # if we had results but have skipped them all, use instrumentalist
                        new_role = "http://www.wikidata.org/entity/Q1278335"
                        new_role_label = "instrumentalist"  
            converted_data.append([row[0], new_role if new_role else row[2], 
                                   new_role_label if new_role_label else row[1]])

    # write result to file
    with open(relative_from_repo_root("resource/instrument_roles_converted.csv"), "w") as f:
        writer = csv.writer(f)
        for row in converted_data:
            writer.writerow(row)


