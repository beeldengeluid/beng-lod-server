from lxml import etree

xsl = "http://www.w3.org/1999/XSL/Transform"
nisv = "http://data.rdlabs.beeldengeluid.nl/schema/"
xs = "http://www.w3.org/2001/XMLSchema#"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
oai_dc = "http://www.openarchives.org/OAI/2.0/oai_dc/"
dc = "http://purl.org/dc/elements/1.1/"
rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
oaipmh = "http://www.openarchives.org/OAI/2.0/"
dcterms = "http://purl.org/dc/terms/"
resource = "http://data.rdlabs.beeldengeluid.nl/resource/"
skos = "http://www.w3.org/2004/02/skos/core#"

ns = {"xsl": xsl,
      "nisv": nisv,
      "xs": xs,
      "xsi": xsi,
      "oai_dc": oai_dc,
      "dc": dc,
      "rdf": rdf,
      "oaipmh": oaipmh,
      "dcterms": dcterms,
      "resource": resource,
      "skos": skos
      }

def set_transform_attributes(transform):
    transform.set("version", "1.0")
    transform.set("exclude-result-prefixes", "oaipmh oai_dc xsl xsi")


def set_output_attributes(output):
    output.set("method", "xml")
    output.set("indent", "yes")
    output.set("encoding", "utf-8")


def add_variable_node(parent, name, select):
    variable_node = etree.SubElement(parent, "{%s}variable"%xsl, nsmap=ns)
    variable_node.set("name", name)
    variable_node.set("select", select)


def add_template(parent, match, namespacePrefix=None):
    template_node = etree.SubElement(parent, "{%s}template"%xsl, nsmap=ns)
    if namespacePrefix:
        template_node.set("match", "%s:%s"%(namespacePrefix, match))
    else:
        template_node.set("match", match)

    return template_node


def add_apply_templates(parent, select=None, namespacePrefix=None):
    apply_template_node = etree.SubElement(parent, "{%s}apply-templates"%xsl, nsmap=ns)
    if select:
        apply_template_node.set("select", "%s:%s"%(namespacePrefix, select), )


def add_test(parent, test):
    test_node = etree.SubElement(parent, "{%s}if"%xsl)
    test_node.set("test", test)
    return test_node


def create_level_option(choose_node, level, levelUri):
    when_node = etree.SubElement(choose_node, "{%s}when"%xsl)
    when_node.set("test", "$level = '%s'"%level)
    element_node = etree.SubElement(when_node, "{%s}element"%xsl)
    element_node.set("name", "rdf:type")
    attribute_node = etree.SubElement(element_node, "{%s}attribute"%xsl)
    attribute_node.set("name", "rdf:resource")
    value_of_node = etree.SubElement(attribute_node, "{%s}value-of"%xsl)
    value_of_node.set("select", levelUri)


def create_resource(parent):
    template_node = etree.SubElement(parent, "{%s}template"%xsl)
    add_variable_node(template_node, "level", "./@aggregationType")
    add_variable_node(template_node, "id", "./@id")

    description_node = etree.SubElement(template_node, "{%s}Description"%rdf)
    about_node = etree.SubElement(description_node, "{%s}attribute"%xsl)
    about_node.set("name", "rdf:about")
    value_of_node = etree.SubElement(about_node, "{%s}value-of"%xsl)
    value_of_node.set("select", "concat($varResource,$level,'/',$id)")
    choose_node = etree.SubElement(description_node, "{%s}choose"%xsl)
    create_level_option(choose_node, "program", "concat($varSchema,'Program')")
    create_level_option(choose_node, "series", "concat($varSchema,'Series')")
    create_level_option(choose_node, "season", "concat($varSchema,'Season')")
    create_level_option(choose_node, "segment", "concat($varSchema,'Segment')")

def create_xslt_from_schema():

    transform = etree.Element("{%s}transform"%xsl, nsmap=ns)
    set_transform_attributes(transform)

    output = etree.SubElement(transform, "{%s}output"%xsl, nsmap=ns)
    set_output_attributes(output)

    strip_space = etree.SubElement(transform, "{%s}strip-space"%xsl, nsmap=ns)
    strip_space.set("elements", "*")

    add_variable_node(transform, "varSchema", "\'%s\'"%nisv)
    add_variable_node(transform, "varResource", "\'%s\'"%resource)

    main_node = add_template(transform, "/")
    add_apply_templates(main_node)

    # Templates for OAI-PMH (container) elements. TODO: Do we really need these?
    oaipmh_node = add_template(transform, "OAI-PMH", "oaipmh")
    add_apply_templates(oaipmh_node)

    list_records_node = add_template(transform, "ListRecords", "oaipmh")
    add_apply_templates(list_records_node)

    get_record_node = add_template(transform, "GetRecord", "oaipmh")
    add_apply_templates(get_record_node)

    # process header and metadata
    record_node = add_template(transform, "record", "oaipmh")
    record_test_node = add_test(record_node, "not(oaipmh:header[@status='deleted'])")
    add_apply_templates(record_test_node, "metadata", "oaipmh")
    add_apply_templates(record_test_node, "header", "oaipmh")
    add_template(transform, "header", "oaipmh")
    metadata_node = add_template(transform, "metadata", "oaipmh")
    add_apply_templates(metadata_node)

    create_resource(transform)
    print(etree.tostring(transform, pretty_print=True, encoding="UTF-8"))

    tree = etree.ElementTree(transform)
    tree.write('test.xsl', encoding='UTF-8', xml_declaration=True, pretty_print=True)
