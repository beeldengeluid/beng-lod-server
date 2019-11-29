import xmltodict
import json

def test_xml_to_json(o_get_record):
    # f = open(o_get_record, "r")
    # xml_string = o_get_record
    # json_string = json.dumps(xmltodict.parse(xml_string))
    json_string = json.dumps(xmltodict.parse(o_get_record.read()))
    print(json_string.replace("fe:", ""))


