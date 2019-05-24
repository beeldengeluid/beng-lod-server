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
	xmlns:nisv= "http://data.rdlabs.beeldengeluid.nl/schema/"
	xmlns:resource= "http://data.rdlabs.beeldengeluid.nl/resource/"
	xmlns:skos= "http://www.w3.org/2004/02/skos/core#"
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
				</xsl:when>
				<xsl:when test="$level = 'season'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource" >
					    	<xsl:value-of select="concat($varSchema,'Season')" />
						</xsl:attribute>
					</xsl:element>
				</xsl:when>
				<xsl:when test="$level = 'series'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource" >
					    	<xsl:value-of select="concat($varSchema,'Series')" />
  					    </xsl:attribute>
					</xsl:element>
				</xsl:when>
				<xsl:when test="$level = 'segment'">
					<xsl:element name="rdf:type">
					    <xsl:attribute name="rdf:resource" >
					    	<xsl:value-of select="concat($varSchema,'Segment')" />
  					    </xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
		  	<xsl:apply-templates />
		</rdf:Description>
	</xsl:template>
	
	<!-- TODO: CHANGE DESCRIPTION HERE Templates for elements that become properties with as range a Class. -->
	<xsl:template match="bg:carrier">
		<xsl:element name="nisv:{local-name()}">
			<xsl:element name="nisv:Carrier">
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:publication">
		<xsl:variable name="publicationID" select="./@id"/>
		<xsl:element name="nisv:{local-name()}">
			<xsl:element name="nisv:Publication">
				<xsl:element name="nisv:id">
					<xsl:value-of select="$publicationID" />
				</xsl:element>
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:recording">
		<xsl:element name="nisv:{local-name()}">
			<xsl:element name="nisv:Recording">
			  	<xsl:apply-templates />
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<!--  TODO template for bg:museum-genre and bg:museum-summary -->

	<!-- SUBCLASSES OF ENTITYINROLE (8)
			TODO:
			In de brondata
				multiple properties
				++
				casts/cast	-> persoon (name, character, clarification)
				speakers/speaker, -> person (name,role)
				executives	->	 bedrijf/persoon (name, role, clarification)
				creators/creator	-> persoon (name, role, clarification, roles) 

				only 'name' property
				++
				sponsors, -> bedrijf	(name)				
				funders -> bedrijf (name)
				producers/producer	-> bedrijf (name)
				contractors/contractor, -> bedrijf	(name)
				
				personnames/personname -> Persoonsnamen (personname)
				names/name -> Namen (name)

				no template
				++
				museum-names	-> will disappear
				museum-personnames	-> will disappear								
				
				
				properties:
				++
				roles/role
				role
				clarification
				character
				
				properties (gelinkt aan de (non-)GTAA):
				++
				personname
				name
	-->

	<!-- NAMES -->
	<xsl:template match="bg:names/bg:name">
		<xsl:element name="nisv:hasOrganisation">
			<xsl:call-template name="SKOSConcept">
				<xsl:with-param name="prefLabel" select="bg:name"/>
			</xsl:call-template>
		</xsl:element>
	</xsl:template>	

	<!-- PERSONNAMES -->
	<xsl:template match="bg:personnames/bg:personname">
		<xsl:element name="nisv:hasPerson">
			<xsl:call-template name="SKOSConcept">
				<xsl:with-param name="prefLabel" select="bg:personname"/>
			</xsl:call-template>
		</xsl:element>
	</xsl:template>	
		
	<!-- CAST -->
	<xsl:template match="bg:cast">
		<xsl:element name="nisv:hasCast">
			<xsl:element name="nisv:Cast">
				<xsl:element name="nisv:hasPerson">
					<xsl:call-template name="SKOSConcept">
						<xsl:with-param name="prefLabel" select="bg:name"/>
					</xsl:call-template>
				</xsl:element>
				<xsl:if test="bg:character">
					<xsl:element name="nisv:hasCharacter">
						<xsl:value-of select="bg:character"/>
					</xsl:element>
				</xsl:if>
				<xsl:if test="bg:clarification">
					<xsl:element name="nisv:hasClarification">
						<xsl:value-of select="bg:clarification"/>
					</xsl:element>
				</xsl:if>
			</xsl:element>
		</xsl:element>
	</xsl:template>	

	<!-- SPEAKER -->
	<xsl:template match="bg:speaker">
		<xsl:element name="nisv:hasSpeaker">
			<xsl:element name="nisv:Speaker">
				<xsl:element name="nisv:hasPerson">
					<xsl:call-template name="SKOSConcept">
						<xsl:with-param name="prefLabel" select="bg:name"/>
					</xsl:call-template>
				</xsl:element>
				<xsl:if test="bg:role">
					<xsl:element name="nisv:hasRole">
						<xsl:value-of select="bg:role"/>
					</xsl:element>
				</xsl:if>
			</xsl:element>
		</xsl:element>
	</xsl:template>	
		
	<!-- PRODUCER -->
	<xsl:template match="bg:producer">
		<xsl:element name="nisv:hasProducer">
			<xsl:element name="nisv:Producer">
				<xsl:element name="nisv:hasOrganisation">
					<xsl:call-template name="SKOSConcept">
						<xsl:with-param name="prefLabel" select="bg:name"/>
					</xsl:call-template>
				</xsl:element>
			</xsl:element>
		</xsl:element>
	</xsl:template>	

	<!-- SPONSOR -->
	<xsl:template match="bg:sponsor">
		<xsl:element name="nisv:hasSponsor">
			<xsl:element name="nisv:Sponsor">
				<xsl:element name="nisv:hasOrganisation">
					<xsl:call-template name="SKOSConcept">
						<xsl:with-param name="prefLabel" select="bg:name"/>
					</xsl:call-template>
				</xsl:element>
			</xsl:element>
		</xsl:element>
	</xsl:template>	
	
	<!-- CONTRACTOR -->
	<xsl:template match="bg:contractor">
		<xsl:element name="nisv:hasContractor">
			<xsl:element name="nisv:Contractor">
				<xsl:element name="nisv:hasOrganisation">
					<xsl:call-template name="SKOSConcept">
						<xsl:with-param name="prefLabel" select="bg:name"/>
					</xsl:call-template>
				</xsl:element>
			</xsl:element>
		</xsl:element>
	</xsl:template>		
	
	<!--  EXECUTIVES -->
	<xsl:template match="bg:executive">
		<xsl:element name="nisv:hasExecutive">
			<xsl:element name="nisv:EntityInRole">
				<xsl:element name="nisv:hasEntity">
					<xsl:call-template name="SKOSConcept">
						<xsl:with-param name="prefLabel" select="bg:name"/>
					</xsl:call-template>
				</xsl:element>
				<xsl:if test="bg:role">
					<xsl:element name="nisv:hasRole">
						<xsl:value-of select="bg:role"/>
					</xsl:element>
				</xsl:if>
				<xsl:if test="bg:clarification">
					<xsl:element name="nisv:hasClarification">
						<xsl:value-of select="bg:clarification"/>
					</xsl:element>
				</xsl:if>
			</xsl:element>
		</xsl:element>
	</xsl:template>	
	
	<!-- CREATOR AND ORIGINALCREATOR 
	-->
 	<xsl:template match="bg:creator | bg:originalCreator">
 		<xsl:variable name="creatorName" select="bg:name"/>		
		<xsl:variable name="creatorClass" select="'Creator'"/>
		<xsl:if test="local-name() = 'originalCreator'">
			<xsl:variable name="creatorClass" select="'OriginalCreator'"/>
		</xsl:if>
 		
		<xsl:choose>
		
	 		<!-- For each roles/role a different Creator (same name)-->
			<xsl:when test="count(bg:roles/bg:role)">
				<xsl:for-each select="bg:roles/bg:role">
					<xsl:element name="nisv:hasCreator">
						<xsl:element name="nisv:{$creatorClass}">
							<xsl:element name="nisv:hasPerson">
								<xsl:call-template name="SKOSConcept">
									<xsl:with-param name="prefLabel" select="$creatorName"/>
								</xsl:call-template>
							</xsl:element>	
							<xsl:if test="self::node()[text()] != ''">
								<xsl:element name="nisv:hasRole">
									<xsl:value-of select="."/>
								</xsl:element>
							</xsl:if>
						</xsl:element>
					</xsl:element>
				</xsl:for-each>
			</xsl:when>

			<!-- For each role a different Creator (same name) -->
			<xsl:when test="count(bg:role)">
				<xsl:for-each select="bg:role">
					<xsl:element name="nisv:hasCreator">
						<xsl:element name="nisv:{$creatorClass}">
							<xsl:element name="nisv:hasPerson">
								<xsl:call-template name="SKOSConcept">
									<xsl:with-param name="prefLabel" select="$creatorName"/>
								</xsl:call-template>
							</xsl:element>	
							<xsl:if test="self::node()[text()] != ''">
								<xsl:element name="nisv:hasRole">
									<xsl:value-of select="."/>
								</xsl:element>
							</xsl:if>
						</xsl:element>
					</xsl:element>
				</xsl:for-each>
			</xsl:when>
			
			<!-- No role, so only a creator with name -->
			<xsl:when test="(count(bg:role) + count(bg:roles/bg:role)) = 0">
				<xsl:element name="nisv:hasCreator">
					<xsl:element name="nisv:{$creatorClass}">
						<xsl:element name="nisv:hasPerson">
							<xsl:call-template name="SKOSConcept">
								<xsl:with-param name="prefLabel" select="$creatorName"/>
							</xsl:call-template>
						</xsl:element>	
					</xsl:element>
				</xsl:element>
			</xsl:when>

			<!-- Just one Creator with a name, no roles -->
			<!-- 
			<xsl:otherwise>
				<xsl:element name="nisv:hasCreator">
					<xsl:element name="nisv:{$creatorClass}">
						<xsl:element name="nisv:hasPerson">
							<xsl:call-template name="SKOSConcept">
								<xsl:with-param name="prefLabel" select="$creatorName"/>
							</xsl:call-template>
						</xsl:element>	
				</xsl:element>
			</xsl:otherwise>
			 -->
			 
		</xsl:choose>
	</xsl:template>	

	<!--  Call templates -->
	<xsl:template name="SKOSConcept">
		<xsl:param name="prefLabel"/>
		<skos:Concept>
			<skos:prefLabel>
				<xsl:value-of select="$prefLabel"/>
			</skos:prefLabel>
		</skos:Concept>
	</xsl:template>
	
 	<!-- END CREATOR -->
 	
	<!--  END SUBCLASSES OF ENTITYINROLE -->

	<!-- Elements that are RDF Properties -->
	<xsl:template match="dc:identifier">
		<dc:identifier>
			<xsl:value-of select="."/>
		</dc:identifier>
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
				<xsl:element name="nisv:isPartOfSeason">
					<xsl:attribute name="rdf:resource">
						 <xsl:value-of select="$uri" />
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
			<xsl:when test="$level = 'program'">
				<xsl:element name="nisv:isPartOfProgram">
					<xsl:attribute name="rdf:resource">
						 <xsl:value-of select="$uri" />
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
			<xsl:when test="$level = 'series'">
				<xsl:element name="nisv:isPartOfSeries">
					<xsl:attribute name="rdf:resource">
						 <xsl:value-of select="$uri" />
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="bg:external-id">
		<xsl:element name="nisv:external-id">
			<xsl:value-of select="."/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:maintitles">
		<xsl:for-each select="bg:title">
			<xsl:element name="nisv:hasMainTitle">
				<xsl:element name="nisv:Title">
					<xsl:element name="nisv:titleValue">
						<xsl:value-of select="."/>
					</xsl:element>
					<xsl:if test="@language" >
						<xsl:element name="nisv:titleLanguage">
							<xsl:value-of select="@language"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@source" >
						<xsl:element name="nisv:titleSource">
							<xsl:value-of select="@source"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@type" >
						<xsl:element name="nisv:titleType">
							<xsl:value-of select="@type"/>
						</xsl:element>
					</xsl:if>
				</xsl:element>
			</xsl:element>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template match="bg:subtitles">
		<xsl:for-each select="bg:title">
			<xsl:element name="nisv:hasSubTitle">
				<xsl:element name="nisv:Title">
					<xsl:element name="nisv:titleValue">
						<xsl:value-of select="."/>
					</xsl:element>
					<xsl:if test="@language" >
						<xsl:element name="nisv:titleLanguage">
							<xsl:value-of select="@language"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@source" >
						<xsl:element name="nisv:titleSource">
							<xsl:value-of select="@source"/>
						</xsl:element>
					</xsl:if>
					<xsl:if test="@type" >
						<xsl:element name="nisv:titleType">
							<xsl:value-of select="@type"/>
						</xsl:element>
					</xsl:if>
				</xsl:element>
			</xsl:element>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template match="bg:productioncountries">
		<xsl:element name="nisv:productioncountries">
		  	<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

	<xsl:template match="bg:language">
		<xsl:choose >
			<!-- Test for a sub element named bg:language -->
			<xsl:when test="bg:language">
				<xsl:element name="nisv:hasLanguage">
					<xsl:element name="nisv:Language">
					  	<xsl:apply-templates />
					</xsl:element>
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="nisv:{local-name()}">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="bg:context">
		<xsl:element name="nisv:hasContext">
			<xsl:element name="nisv:Context">
				<xsl:for-each select="./*">
					<xsl:element name="nisv:{local-name()}">
						<xsl:value-of select="."/>
					</xsl:element>
				</xsl:for-each>
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="bg:productioncountries">
		<xsl:element name="nisv:productioncountries">
			<xsl:element name="nisv:Productioncountry">
				<xsl:for-each select="bg:country">
					<xsl:element name="nisv:country">
						<xsl:value-of select="."/>
					</xsl:element>
				</xsl:for-each>
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<!--  For now, do not include transcripts.  -->
	<xsl:template match="bg:transcripts"/>
	
	<!-- A generic template to remove all elements that are only there to support sequences in XML. 
		For matching pattern see: Eg. https://stackoverflow.com/questions/1007018/xslt-expression-to-check-if-variable-belongs-to-set-of-elements
		
		TODO: roles can be out of the list?
	-->
	<xsl:template match="bg:*">
		<xsl:variable name="list" select="'recordings producers funders sponsors contractors carriers languages creators roles publications genres networks broadcasters'" />
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
						<xsl:call-template name="leaveElement"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template name="leaveElement">
		<!-- Date/time elements are handled a little bit different. 
			Dates are encoded as '2018-01-30T11:39:14Z'
			TODO: Years, duration, startoncarrier, etc.
		-->
		<xsl:variable name="dateElements" select="'startdate enddate montagedate creationdate datereceived sortdate'" />
		<xsl:variable name="timeElements" select="'starttime endtime starttimestamp'" />
		<xsl:variable name="elem" select="local-name()" />
		
		<xsl:choose> 
			<xsl:when test="contains( concat(' ', $dateElements, ' '), concat(' ', $elem, ' ') ) ">
				<xsl:element name="nisv:{local-name()}" type="xsd:dateTime">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="contains( concat(' ', $timeElements, ' '), concat(' ', $elem, ' ') ) ">
				<xsl:element name="nisv:{local-name()}" type="xsd:time">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:otherwise>
				<xsl:element name="nisv:{local-name()}">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:otherwise>

		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="text()"/>

</xsl:transform>
