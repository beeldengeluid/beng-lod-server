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
	xmlns:bga= "http://oaipmh.beeldengeluid.nl/aggregated"
	xmlns:schema= "http://data.rdlabs.beeldengeluid.nl/schema/"
	xmlns:resource= "http://data.rdlabs.beeldengeluid.nl/resource/"
	exclude-result-prefixes="oaipmh oai_dc xsl xsi bg bga">

	<xsl:output method="xml" indent="yes" encoding="utf-8"/>
	<xsl:strip-space elements="*"/>

	<xsl:variable name="varSchema" select= "'http://data.rdlabs.beeldengeluid.nl/schema/'" />
	<xsl:variable name="varResource" select= "'http://data.rdlabs.beeldengeluid.nl/resource/'" />
	
	<xsl:template match="/" >
	  	<xsl:apply-templates />
	</xsl:template>
	
	<!-- Templates for OAI-PMH (container) elements. -->

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
	
	<!-- Templates for element that are converted to RDF Classes -->
	
	<xsl:template match="bg:bgelement">
		<xsl:variable name="level" select="./@aggregationType"/>
		<xsl:variable name="id" select="./@id"/>

		<rdf:Description>
			<xsl:attribute name="rdf:about">
				<xsl:value-of select="concat($varResource,$level,'/',$id)" />
			</xsl:attribute>
			<xsl:choose>
				<xsl:when test="$level = 'program'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource">
					    	<xsl:value-of select="concat($varSchema,'Program')" />
					    </xsl:attribute>
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
				<xsl:when test="$level = 'season'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource" >
					    	<xsl:value-of select="concat($varSchema,'Season')" />
						</xsl:attribute>
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
				<xsl:when test="$level = 'series'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource" >
					    	<xsl:value-of select="concat($varSchema,'Series')" />
  					    </xsl:attribute>
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
				<xsl:when test="$level = 'segment'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource" >
					    	<xsl:value-of select="concat($varSchema,'Segment')" />
  					    </xsl:attribute>
					</xsl:element>
				  	<xsl:apply-templates />
				</xsl:when>
			</xsl:choose>
		</rdf:Description>
	</xsl:template>
	
	<!-- Templates for elements that become properties with as range a Class. -->
	<xsl:template match="bg:carrier">
		<xsl:element name="schema:{local-name()}">
			<xsl:element name="schema:Carrier">
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:publication">
		<xsl:variable name="id" select="./@id"/>
		<xsl:element name="schema:{local-name()}">
			<xsl:element name="schema:Publication">
				<xsl:element name="schema:id">
					<xsl:value-of select="$id" />
				</xsl:element>
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:recording">
		<xsl:element name="schema:{local-name()}">
			<xsl:element name="schema:Recording">
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:creator">
		<xsl:element name="schema:{local-name()}">
			<xsl:element name="schema:Creator">
				<!--  TODO: find the skos concept URI. -->
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>	
 
	<!-- Elements that are RDF Properties -->
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

	<xsl:template match="dcterms:isPartOf">
		<xsl:variable name="resourceID" select="." />
		<xsl:variable name="levelID" select="substring-before(substring-after($resourceID,'resource/'),'?')"/>
		<xsl:variable name="uri" select="concat($varResource,$levelID)"/>
		<xsl:variable name="level" select="substring-before($levelID, '/')"/>
		<xsl:choose>
			<xsl:when test="$level = 'season'">
				<xsl:element name="schema:isPartOfSeason">
					<xsl:attribute name="rdf:resource">
						 <xsl:value-of select="$uri" />
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
			<xsl:when test="$level = 'program'">
				<xsl:element name="schema:isPartOfProgram">
					<xsl:attribute name="rdf:resource">
						 <xsl:value-of select="$uri" />
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
			<xsl:when test="$level = 'series'">
				<xsl:element name="schema:isPartOfSeries">
					<xsl:attribute name="rdf:resource">
						 <xsl:value-of select="$uri" />
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="bg:external-id">
		<xsl:element name="schema:external-id">
			<xsl:value-of select="."/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:maintitles">
		<xsl:for-each select="bg:title">
			<xsl:element name="schema:hasMainTitle">
				<xsl:element name="schema:Title">
					<xsl:element name="schema:titleValue">
						<xsl:value-of select="."/>
					</xsl:element>
					<xsl:if test="@language" >
						<xsl:element name="schema:titleLanguage">
							<xsl:value-of select="@language"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@source" >
						<xsl:element name="schema:titleSource">
							<xsl:value-of select="@source"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@type" >
						<xsl:element name="schema:titleType">
							<xsl:value-of select="@type"/>
						</xsl:element>
					</xsl:if>
				</xsl:element>
			</xsl:element>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template match="bg:subtitles">
		<xsl:for-each select="bg:title">
			<xsl:element name="schema:hasSubTitle">
				<xsl:element name="schema:Title">
					<xsl:element name="schema:titleValue">
						<xsl:value-of select="."/>
					</xsl:element>
					<xsl:if test="@language" >
						<xsl:element name="schema:titleLanguage">
							<xsl:value-of select="@language"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@source" >
						<xsl:element name="schema:titleSource">
							<xsl:value-of select="@source"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@type" >
						<xsl:element name="schema:titleType">
							<xsl:value-of select="@type"/>
						</xsl:element>
					</xsl:if>
				</xsl:element>
			</xsl:element>
		</xsl:for-each>
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
				<xsl:element name="schema:hasLanguage">
					<xsl:element name="schema:Language">
					  	<xsl:apply-templates />
					</xsl:element>
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="schema:{local-name()}">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="bg:context">
		<xsl:element name="schema:hasContext">
			<xsl:element name="schema:Context">
				<xsl:for-each select="./*">
					<xsl:element name="schema:{local-name()}">
						<xsl:value-of select="."/>
					</xsl:element>
				</xsl:for-each>
			</xsl:element>
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:producer">
		<xsl:element name="schema:producer">
			<xsl:element name="schema:Producer">
				<xsl:for-each select="bg:name">
					<xsl:element name="schema:hasName">
						<xsl:value-of select="."/>
					</xsl:element>
				</xsl:for-each>
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:productioncountries">
		<xsl:element name="schema:productioncountries">
			<xsl:element name="schema:Productioncountry">
				<xsl:for-each select="bg:country">
					<xsl:element name="schema:country">
						<xsl:value-of select="."/>
					</xsl:element>
				</xsl:for-each>
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:transcripts"/>
	
	<!-- A generic template to remove all elements that are only there to support sequences in XML. 
		For matching pattern see: Eg. https://stackoverflow.com/questions/1007018/xslt-expression-to-check-if-variable-belongs-to-set-of-elements
	-->
	<xsl:template match="bg:*">
		<xsl:variable name="list" select="'recordings producers carriers languages creators roles publications genres networks broadcasters'" />
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
