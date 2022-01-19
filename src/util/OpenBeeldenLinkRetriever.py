import json
import re
import numpy as np
import sys

from elasticsearch import Elasticsearch
from elasticsearch import helpers


def levenshtein_ratio_and_distance(s, t, ratio_calc=False):
    """levenshtein_ratio_and_distance:
    Calculates levenshtein distance between two strings.
    If ratio_calc = True, the function computes the
    levenshtein distance ratio of similarity between two strings
    For all i and j, distance[i,j] will contain the Levenshtein
    distance between the first i characters of s and the
    first j characters of t
    """
    # Initialize matrix of zeros
    rows = len(s) + 1
    cols = len(t) + 1
    distance = np.zeros((rows, cols), dtype=int)

    # Populate matrix of zeros with the indices of each character of both strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row - 1] == t[col - 1]:
                # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
                cost = 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to
                # calculate the ratio the cost of a substitution is 2. If we calculate just distance, then the
                # cost of a substitution is 1.
                if ratio_calc:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(
                distance[row - 1][col] + 1,  # Cost of deletions
                distance[row][col - 1] + 1,  # Cost of insertions
                distance[row - 1][col - 1] + cost,
            )  # Cost of substitutions

    # TODO: row and col not in scope
    if ratio_calc:
        # Computation of the Levenshtein Distance Ratio
        ratio = ((len(s) + len(t)) - distance[row][col]) / (len(s) + len(t))
        return ratio
    else:
        # print(distance) # Uncomment if you want to see the matrix showing how
        # the algorithm computes the cost of deletions, insertions and/or substitutions
        # This is the minimum number of edits needed to convert string a to string b
        return "The strings are {} edits away".format(distance[row][col])


def titles_match(title1, title2, threshold):
    title1_stripped = strip_string(title1)
    title2_stripped = strip_string(title2)

    if (
        title1_stripped == title2_stripped
        or title1_stripped in title2_stripped
        or title2_stripped in title1_stripped
    ):
        return True
    match_score = levenshtein_ratio_and_distance(
        title1_stripped, title2_stripped, ratio_calc=True
    )
    if match_score * 100 > threshold:
        return True
    else:
        return False


def strip_string(text):
    pattern = r"[^A-Za-z0-9]+"
    text = text.replace("&quot;", "")
    text = text.replace("½", ",5")
    text = re.sub(pattern, "", text)
    text = text.lower()
    text = text.replace("y", "ij")
    text = text.replace("NEGENTIEN TWEE EN DERTIG", "1932")
    return text


def generate_candidate_queries(ob_source_list, result):
    candidate_carrier_queries = []
    for ob_source in ob_source_list:
        candidate_carrier_queries.append(
            {
                "query": {
                    "bool": {
                        "must": [{"term": {"assetItems.carriernumber": ob_source}}]
                    }
                }
            }
        )
        candidate_carrier_queries.append(
            {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"assetItems.carriernumber": ob_source + ".mxf"}}
                        ]
                    }
                }
            }
        )
        candidate_carrier_queries.append(
            {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"assetItems.carriernumber": ob_source.upper()}}
                        ]
                    }
                }
            }
        )
        candidate_carrier_queries.append(
            {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "assetItems.carriernumber": ob_source.upper()
                                    + ".mxf"
                                }
                            }
                        ]
                    }
                }
            }
        )
        new_ref = ob_source
        if "_" in new_ref and re.search(r"[0-9]_[0-9]", new_ref):
            new_ref = re.split(r"[_](?=[0-9])", new_ref)[0]
        if "." in new_ref:
            new_ref = new_ref.split(".")[0]
        candidate_carrier_queries.append(
            {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"assetItems.carriernumber": new_ref.upper()}}
                        ]
                    }
                }
            }
        )

    if "dcterms:hasFormat" in result["_source"]["@graph"]:
        if type(result["_source"]["@graph"]["dcterms:hasFormat"]) == list:
            format_list = result["_source"]["@graph"]["dcterms:hasFormat"]
        else:
            format_list = [result["_source"]["@graph"]["dcterms:hasFormat"]]

        for format in format_list:
            if len(format.split(".")) > 4:
                hasFormatTest = format.split(".")[4]
            else:
                hasFormatTest = format
            if "_" in hasFormatTest and re.search(r"[0-9]_[0-9]", hasFormatTest):
                hasFormatTest = re.split(r"[_](?=[0-9])", hasFormatTest)[0]
                candidate_carrier_queries.append(
                    {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "term": {
                                            "assetItems.carriernumber": hasFormatTest
                                        }
                                    }
                                ]
                            }
                        }
                    }
                )

            if "Steegjes" in hasFormatTest:
                hasFormatTest = hasFormatTest.split("_")[1]

            mpg_ref = hasFormatTest + ".mpg"
            candidate_carrier_queries.append(
                {
                    "query": {
                        "bool": {
                            "must": [{"term": {"assetItems.carriernumber": mpg_ref}}]
                        }
                    }
                }
            )
            candidate_carrier_queries.append(
                {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "assetItems.carriernumber": mpg_ref.replace(
                                            "_", "-"
                                        )
                                    }
                                }
                            ]
                        }
                    }
                }
            )
            mxf_ref = hasFormatTest + ".mxf"
            candidate_carrier_queries.append(
                {
                    "query": {
                        "bool": {
                            "must": [{"term": {"assetItems.carriernumber": mxf_ref}}]
                        }
                    }
                }
            )
            candidate_carrier_queries.append(
                {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "assetItems.carriernumber": mxf_ref.replace(
                                            "_", "-"
                                        )
                                    }
                                }
                            ]
                        }
                    }
                }
            )

    if "dcterms:identifier" in result["_source"]["@graph"]:
        identifier = result["_source"]["@graph"]["dcterms:identifier"]
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"dc:identifier": identifier}}]}}}
        )
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"program.site_id": identifier}}]}}}
        )
    return candidate_carrier_queries


def get_content_link(result):
    ob_link = ""
    if "dcterms:hasFormat" in result["_source"]["@graph"]:
        if type(result["_source"]["@graph"]["dcterms:hasFormat"]) == list:
            format_list = result["_source"]["@graph"]["dcterms:hasFormat"]
        else:
            format_list = [result["_source"]["@graph"]["dcterms:hasFormat"]]
        for hasFormat in format_list:
            if hasFormat.endswith("mp4"):
                if not ob_link:
                    ob_link = hasFormat
                elif len(hasFormat) < len(
                    ob_link
                ):  # shortest filename usually source file
                    ob_link = hasFormat
    return ob_link


def get_website(result):
    website = ""
    if "cc:attributionURL" in result["_source"]["@graph"]:
        website = result["_source"]["@graph"]["cc:attributionURL"]

    return website


def get_title(result):
    ob_title = ""
    if isinstance(result["_source"]["@graph"]["dcterms:title"], list):
        for title in result["_source"]["@graph"]["dcterms:title"]:
            if title["@language"] == "nl":
                ob_title = title["@value"]
    else:
        ob_title = result["_source"]["@graph"]["dcterms:title"]["@value"]
    return ob_title


def get_source_list(result):
    ob_source_list = []
    if "dcterms:source" in result["_source"]["@graph"]:
        ob_source_json = result["_source"]["@graph"]["dcterms:source"]
        if type(ob_source_json) == list:
            ob_source_list = [source_item["@value"] for source_item in ob_source_json]
        else:
            ob_source_list = [ob_source_json["@value"]]

    return ob_source_list


if __name__ == "__main__":
    print(sys.argv)
    __es = Elasticsearch(host=sys.argv[1], port=sys.argv[2])

    daan_catalogue = "daan-catalogue-aggr"
    open_beelden_catalogue = "open-beelden-beeldengeluid"

    matches = {}

    query = {
        "_source": [
            "@graph.dcterms:source",
            "@graph.dcterms:hasFormat",
            "@graph.dcterms:identifier",
            "@graph.dcterms:title",
            "@graph.cc:attributionURL",
        ],
        "query": {"bool": {"must": [{"match_all": {}}]}},
    }
    resp = helpers.scan(__es, query, index=open_beelden_catalogue)

    count = 0
    match_count = 0
    program_level_match_count = 0
    scene_description_level_match_count = 0
    fails = []
    for result in resp:
        successful_query = {}

        ob_id = result["_id"]
        ob_title = get_title(result)
        ob_source_list = get_source_list(result)
        ob_content_link = get_content_link(result)
        ob_website = get_website(result)

        # # Now Find It!
        if count >= 0:
            daan_ids = []
            candidate_carrier_queries = generate_candidate_queries(
                ob_source_list, result
            )

            found_match = False
            index = 0
            for carrier_query in candidate_carrier_queries:
                searchResp = __es.search(index=daan_catalogue, body=carrier_query)
                if searchResp["hits"]["total"]["value"] >= 1:
                    for daan_result in searchResp["hits"]["hits"]:
                        daan_ids.append(daan_result["_id"])
                        found_match = True
                        successful_query = carrier_query
                    break
                index += 1

            if found_match:
                for daan_id in daan_ids:
                    matched_id = daan_id
                    local_match_count = 0
                    scene_descs = False
                    if "assetItems.carriernumber" in json.dumps(successful_query):
                        matched_carrier_number = successful_query["query"]["bool"][
                            "must"
                        ][0]["term"]["assetItems.carriernumber"]
                        if len(matched_carrier_number) <= 3:
                            print(f"Skipping {matched_carrier_number} as ambiguous")
                            continue
                        # get the scene descriptions and their titles to see if we can match more specifically
                        scene_descriptions_query = {
                            "_source": ["assetItems", "logTrackItems.ltSceneDesc"],
                            "query": {
                                "bool": {
                                    "must": [
                                        {"term": {"_id": daan_id}},
                                        {
                                            "exists": {
                                                "field": "logTrackItems.ltSceneDesc"
                                            }
                                        },
                                    ]
                                }
                            },
                        }
                        scene_resp = helpers.scan(
                            __es, scene_descriptions_query, index=daan_catalogue
                        )

                        scene_descs = False
                        # try to match a scene description title. If not, just link on programme level
                        for prog_result in scene_resp:
                            scene_descs = True
                            if ob_title == "Ontdek uw stad-tentoonstelling":
                                print("wait")
                            # get the carrier ID that had matched in the query
                            matched_carrier_id = ""
                            for carrier_result in prog_result["_source"]["assetItems"]:
                                if (
                                    "carriernumber" in carrier_result
                                    and carrier_result["carriernumber"][0]
                                    == matched_carrier_number
                                ):
                                    matched_carrier_id = carrier_result["id"]

                            local_match_count = 0
                            for scene_result in prog_result["_source"]["logTrackItems"][
                                "ltSceneDesc"
                            ]:
                                if "title" in scene_result:
                                    for scene_title in scene_result["title"]:
                                        if titles_match(scene_title, ob_title, 70):
                                            # we do NOT check for a carrier match, we assume that as there is already
                                            # a link at programme level, any scene description that matches on title
                                            # is good
                                            # use the scene description ID for the link
                                            print(f"Using {scene_title} for {ob_title}")
                                            matched_id = scene_result["id"]
                                            local_match_count += 1
                        if local_match_count > 1:
                            print("WARNING: ambiguous matches for scene description")
                    if matched_id == daan_id:
                        program_level_match_count += 1
                        print("Matching on programme level")
                        if not scene_descs:
                            print("no scene descriptions")
                    else:
                        scene_description_level_match_count += 1
                    match_count += 1
                    if matched_id in matches:
                        if ob_content_link not in matches[matched_id]["content_links"]:
                            matches[matched_id]["content_links"].append(ob_content_link)
                        matches[matched_id]["sources"].extend(ob_source_list)
                    else:
                        matches[matched_id] = {}
                        matches[matched_id]["content_links"] = [ob_content_link]
                        matches[matched_id]["sources"] = ob_source_list
                        matches[matched_id]["website"] = ob_website
            else:
                fails.append(ob_id)
            print(f"{count}")
        count += 1
    print(f"Processed {count}")
    print(f"Matches {match_count}")
    print(f"\t of which {program_level_match_count} on programme level")
    print(f"\t and {scene_description_level_match_count} on scene description level")
    print(f"Missed {len(fails)}")

    with open("fails.json", "w") as fail_file:
        fail_file.write(json.dumps(fails))

    with open("matches.json", "w") as match_file:
        match_file.write(json.dumps(matches))
