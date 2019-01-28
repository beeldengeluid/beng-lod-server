<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" 
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	xmlns:oaipmh="http://www.openarchives.org/OAI/2.0/" 
	xmlns:dcterms="http://purl.org/dc/terms/"
	xmlns:bg= "http://oaipmh.beeldengeluid.nl/basic"
	xmlns:bgmod= "http://data.rdlabs.nl/schema/"
	xmlns:bgres= "http://data.rdlabs.nl/resource/"
	exclude-result-prefixes="oaipmh oai_dc xsl xsi">

	<xsl:output method="xml" indent="yes" encoding="utf-8"/>
	<xsl:strip-space elements="*"/>

	<xsl:template match="/" >
	  	<xsl:apply-templates />
	</xsl:template>

	<xsl:template match="bg:bgelement">
		<xsl:variable name="level" select="@aggregationType"/>
		<xsl:variable name="id" select="@id"/>
		<xsl:variable name="uri" select="concat('bgres:','/',$level,'/',$id)"/>

		<rdf:RDF>
			<rdf:Description>
				<xsl:attribute name="rdf:about">
					<xsl:value-of select="$uri" />
				</xsl:attribute>
			  	<xsl:apply-templates />
			</rdf:Description>
		</rdf:RDF>
	</xsl:template>

	<xsl:template match="dc:identifier">
		<xsl:copy-of select="."/>
	</xsl:template>

	<xsl:template match="text()"/>

</xsl:transform>
