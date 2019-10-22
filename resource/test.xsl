<?xml version='1.0' encoding='UTF-8'?>
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:nisv="http://data.rdlabs.beeldengeluid.nl/schema/" xmlns:xs="http://www.w3.org/2001/XMLSchema#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:oaipmh="http://www.openarchives.org/OAI/2.0/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:resource="http://data.rdlabs.beeldengeluid.nl/resource/" xmlns:skos="http://www.w3.org/2004/02/skos/core#" version="1.0" exclude-result-prefixes="oaipmh oai_dc xsl xsi">
  <xsl:output method="xml" indent="yes" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>
  <xsl:variable name="varSchema" select="'http://data.rdlabs.beeldengeluid.nl/schema/'"/>
  <xsl:variable name="varResource" select="'http://data.rdlabs.beeldengeluid.nl/resource/'"/>
  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="oaipmh:OAI-PMH">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="oaipmh:ListRecords">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="oaipmh:GetRecord">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="oaipmh:record">
    <xsl:if test="not(oaipmh:header[@status='deleted'])">
      <xsl:apply-templates select="oaipmh:metadata"/>
      <xsl:apply-templates select="oaipmh:header"/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="oaipmh:header"/>
  <xsl:template match="oaipmh:metadata">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template>
    <xsl:variable name="level" select="./@aggregationType"/>
    <xsl:variable name="id" select="./@id"/>
    <rdf:Description>
      <xsl:attribute name="rdf:about">
        <xsl:value-of select="concat($varResource,$level,'/',$id)"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$level = 'program'">
          <xsl:element name="rdf:type">
            <xsl:attribute name="rdf:resource">
              <xsl:value-of select="concat($varSchema,'Program')"/>
            </xsl:attribute>
          </xsl:element>
        </xsl:when>
        <xsl:when test="$level = 'series'">
          <xsl:element name="rdf:type">
            <xsl:attribute name="rdf:resource">
              <xsl:value-of select="concat($varSchema,'Series')"/>
            </xsl:attribute>
          </xsl:element>
        </xsl:when>
        <xsl:when test="$level = 'season'">
          <xsl:element name="rdf:type">
            <xsl:attribute name="rdf:resource">
              <xsl:value-of select="concat($varSchema,'Season')"/>
            </xsl:attribute>
          </xsl:element>
        </xsl:when>
        <xsl:when test="$level = 'segment'">
          <xsl:element name="rdf:type">
            <xsl:attribute name="rdf:resource">
              <xsl:value-of select="concat($varSchema,'Segment')"/>
            </xsl:attribute>
          </xsl:element>
        </xsl:when>
      </xsl:choose>
    </rdf:Description>
  </xsl:template>
</xsl:transform>
