import xmltodict
import json

def test_xml_to_json(o_get_record):
    xml_string = o_get_record.read()
    json_string = json.dumps(xmltodict.parse(xml_string))
    print(json_string.replace("fe:", ""))


