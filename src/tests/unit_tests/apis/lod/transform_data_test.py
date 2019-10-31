import xmltodict
import json

def test_xml_to_json(get_record_xml_local_uri):
    f = open(get_record_xml_local_uri, "r")
    xml_string = f.read()
    json_string = json.dumps(xmltodict.parse(xml_string))
    print(json_string.replace("fe:", ""))


