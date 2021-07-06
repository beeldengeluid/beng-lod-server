import json
import re
import sys
from elasticsearch import Elasticsearch
from elasticsearch import helpers


def generate_candidate_queries(ob_source_list, result):
    candidate_carrier_queries = []
    for ob_source in ob_source_list:
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"assetItems.carriernumber": ob_source}}]}}})
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"assetItems.carriernumber": ob_source + ".mxf"}}]}}})
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"assetItems.carriernumber": ob_source.upper()}}]}}})
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"assetItems.carriernumber": ob_source.upper() + ".mxf"}}]}}})
        new_ref = ob_source
        if "_" in new_ref and re.search(r'[0-9]_[0-9]', new_ref):
            new_ref = re.split(r'[_](?=[0-9])', new_ref)[0]
        if "." in new_ref:
            new_ref = new_ref.split(".")[0]
        candidate_carrier_queries.append(
            {"query": {"bool": {"must": [{"term": {"assetItems.carriernumber": new_ref.upper()}}]}}})

    if "dcterms:hasFormat" in result['_source']['@graph']:
        if type(result['_source']['@graph']['dcterms:hasFormat']) == list:
            format_list = result['_source']['@graph']['dcterms:hasFormat']
        else:
            format_list = [result['_source']['@graph']['dcterms:hasFormat']]

        for format in format_list:
            if len(format.split(".")) > 4:
                hasFormatTest = format.split(".")[4]
            else:
                hasFormatTest = format
            if "_" in hasFormatTest and re.search(r'[0-9]_[0-9]', hasFormatTest):
                hasFormatTest = re.split(r'[_](?=[0-9])', hasFormatTest)[0]
                candidate_carrier_queries.append({
                    "query": {"bool": {"must": [{"term": {"assetItems.carriernumber": hasFormatTest}}]}}})

            if "Steegjes" in hasFormatTest:
                hasFormatTest = hasFormatTest.split("_")[1]

            mpg_ref = hasFormatTest + ".mpg"
            candidate_carrier_queries.append({"query": {"bool": {
            "must": [{"term": {"assetItems.carriernumber": mpg_ref}}]}}})
            candidate_carrier_queries.append({"query": {"bool": {
            "must": [{"term": {"assetItems.carriernumber": mpg_ref.replace("_", "-")}}]}}})
            mxf_ref = hasFormatTest + ".mxf"
            candidate_carrier_queries.append({"query": {"bool": {
                "must": [{"term": {"assetItems.carriernumber": mxf_ref}}]}}})
            candidate_carrier_queries.append({"query": {"bool": {
            "must": [{"term": {"assetItems.carriernumber": mxf_ref.replace("_", "-")}}]}}})

    if 'dcterms:identifier' in result['_source']['@graph']:
        identifier = result['_source']['@graph']['dcterms:identifier']
        candidate_carrier_queries.append({"query": {"bool": {"must": [{"term": {"dc:identifier": identifier}}]}}})
        candidate_carrier_queries.append({"query": {"bool": {"must": [{"term": {"program.site_id": identifier}}]}}})
    return candidate_carrier_queries

def get_link(result):
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
                elif len(hasFormat) < len(ob_link):  # shortest filename usually source file
                    ob_link = hasFormat
    return ob_link

if __name__ == '__main__':
    print(sys.argv)
    __es = Elasticsearch(
        host=sys.argv[1],
        port=sys.argv[2]
    )

    daan_catalogue = "daan-catalogue-aggr"
    open_beelden_catalogue = "open-beelden-beeldengeluid"

    matches = {}

    query = {"_source": ["@graph.dcterms:source", "@graph.dcterms:hasFormat", "@graph.dcterms:identifier"],
             "query": {
                 "bool": {
                     "must": [
                         {
                             "match_all": {}
                         }
                     ]
                 }
             }
    }
    resp = helpers.scan(__es, query, index=open_beelden_catalogue, doc_type="rdf")

    count = 0
    fails = []
    for result in resp:
        ob_id = result["_id"]
        ob_source_list = []
        ob_link = ""

        if "dcterms:source" in result["_source"]["@graph"]:
            ob_source_json = result["_source"]["@graph"]["dcterms:source"]
            if type(ob_source_json) == list:
                ob_source_list = [source_item["@value"] for source_item in ob_source_json]
            else:
                ob_source_list = [ob_source_json["@value"]]
        ob_link = get_link(result)

        # # Now Find It!
        daan_ids = []
        candidate_carrier_queries = generate_candidate_queries(ob_source_list, result)

        found_match = False
        index = 0
        for carrier_query in candidate_carrier_queries:
            searchResp = __es.search(daan_catalogue, "aggregated-program", body=carrier_query)
            if searchResp['hits']['total'] >= 1:
                for daan_result in searchResp['hits']['hits']:
                    daan_ids.append(daan_result["_id"])
                    found_match = True
                break
            index += 1

        if found_match:
            for daan_id in daan_ids:
                if daan_id in matches:
                    if ob_link not in matches[daan_id]["links"]:
                        matches[daan_id]["links"].append(ob_link)
                    matches[daan_id]["sources"].extend(ob_source_list)
                else:
                    matches[daan_id] = {}
                    matches[daan_id]["links"] = [ob_link]
                    matches[daan_id]["sources"] = ob_source_list
        else:
            fails.append(ob_id)

        count += 1
    print(f"Processed {count}")
    print(f"Matches {len(matches)}")
    print(f"Missed {len(fails)}")

    with open("fails.json", "w") as fail_file:
        fail_file.write(json.dumps(fails))

    with open("matches.json", "w") as match_file:
        match_file.write(json.dumps(matches))
