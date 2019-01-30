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
	xmlns:schema= "http://data.rdlabs.beeldengeluid.nl/schema/"
	xmlns:bgres= "http://data.rdlabs.beeldengeluid.nl/resource/"
	exclude-result-prefixes="oaipmh oai_dc xsl xsi">

	<xsl:output method="xml" indent="yes" encoding="utf-8"/>
	<xsl:strip-space elements="*"/>

	<xsl:template match="/" >
	  	<xsl:apply-templates />
	</xsl:template>

	<xsl:template match="oaipmh:OAI-PMH">
		<rdf:RDF>	
			<xsl:apply-templates />
		</rdf:RDF>
	</xsl:template>

	<xsl:template match="oaipmh:ListRecords">
  		<xsl:apply-templates />
	</xsl:template>
	
	<xsl:template match="oaipmh:GetRecord">
	  	<xsl:apply-templates />
	</xsl:template>
	
	<xsl:template match="oaipmh:record">
		<xsl:if test="not(oaipmh:header[@status='deleted'])">
			<xsl:apply-templates select="oaipmh:metadata" />
			<xsl:apply-templates select="oaipmh:header" />
		</xsl:if>
	</xsl:template>
	
	<xsl:template match="oaipmh:header"/>

	<xsl:template match="oaipmh:metadata">
		<xsl:apply-templates />
	</xsl:template>
	
	<xsl:template match="bg:bgelement">
		<xsl:variable name="level" select="./@aggregationType"/>
		<xsl:variable name="id" select="./@id"/>

		<rdf:Description>
			<xsl:attribute name="rdf:about">
				<xsl:value-of select="concat('http://data.rdlabs.beeldengeluid.nl/resource/',$level,'/',$id)" />
			</xsl:attribute>
			<xsl:choose>
				<xsl:when test="$level = 'program'">
					<xsl:element name="rdf:type">
					 	<xsl:value-of select="schema:Program" />
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
				<xsl:when test="$level = 'season'">
					<xsl:element name="rdf:type">
					 	<xsl:value-of select="schema:Season" />
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
				<xsl:when test="$level = 'series'">
					<xsl:element name="rdf:type">
					 	<xsl:value-of select="schema:Series" />
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
				<xsl:when test="$level = 'segment'">
					<xsl:element name="rdf:type">
					 	<xsl:value-of select="schema:Segment" />
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
			</xsl:choose>
		</rdf:Description>
	</xsl:template>

	<xsl:template match="dc:identifier">
		<xsl:copy-of select="."/>
	</xsl:template>

	<xsl:template match="dc:relation">
		<xsl:element name="{name()}">
			<xsl:attribute name="rdf:resource">
				<xsl:value-of select="." />
			</xsl:attribute>
		</xsl:element>
	</xsl:template>

	<!-- TODO rewrite the parent URI -->
	<xsl:template match="dcterms:isPartOf">
		<xsl:element name="{name()}">
				<xsl:attribute name="rdf:resource">
					<xsl:value-of select="." />
				</xsl:attribute>
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:external-id">
		<xsl:element name="schema:external-id">
			<xsl:value-of select="."/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:maintitles">
	  	<xsl:apply-templates />
	</xsl:template>

	<xsl:template match="bg:productioncountries">
		<xsl:element name="schema:productioncountries">
		  	<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:language">
		<xsl:choose >
			<!-- Test for a sub element named bg:language -->
			<xsl:when test="bg:language">
			  	<xsl:apply-templates />
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="schema:language">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="bg:context">
		<xsl:element name="schema:context">
		  	<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

	<!-- A generic template for all elements that are only there to validate the sequence in XML. 
		For matching pattern see: Eg. https://stackoverflow.com/questions/1007018/xslt-expression-to-check-if-variable-belongs-to-set-of-elements
	-->
	<xsl:template match="bg:*">
		<xsl:variable name="list" select="'recordings producers carriers languages creators roles publications genres networks'" />
		<xsl:variable name="k" select="local-name()" />
		<xsl:choose> 
			<xsl:when test="contains( concat(' ', $list, ' '), concat(' ', $k, ' ') ) ">
			  	<xsl:apply-templates />
			</xsl:when>
			<xsl:otherwise>
				<xsl:choose>
					<xsl:when test="*">
					  <xsl:apply-templates />
					</xsl:when>
					<xsl:otherwise>
						<xsl:element name="schema:{local-name()}">
							<xsl:value-of select="."/>
						</xsl:element>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
 	</xsl:template>
	
	<xsl:template match="text()"/>

</xsl:transform>
