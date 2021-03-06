<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xs="http://www.w3.org/2001/XMLSchema#"
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
	
	<!-- Properties of the AudioVisualObject with a Class as range.	-->
	<xsl:template match="bg:carrier">
		<nisv:hasCarrier>
			<nisv:Carrier>
			  	<xsl:apply-templates />
			</nisv:Carrier>
		</nisv:hasCarrier>
	</xsl:template>
	
	<xsl:template match="bg:publication">
		<xsl:variable name="publicationID" select="./@id"/>
		<nisv:hasPublication>
			<nisv:Publication>
				<xsl:element name="nisv:id">
					<xsl:value-of select="$publicationID" />
				</xsl:element>
			  	<xsl:apply-templates />
			</nisv:Publication>
		</nisv:hasPublication>
	</xsl:template>
	
	<xsl:template match="bg:recording">
		<nisv:hasRecording>
			<nisv:Recording>
			  	<xsl:apply-templates />
			</nisv:Recording>
		</nisv:hasRecording>
	</xsl:template>
	
	<!--  TODO template for bg:museum-genre and bg:museum-summary -->

	<!-- SUBCLASSES OF ENTITYINROLE (8)
			In de brondata
				multiple properties
				++

				only 'name' property
				++

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

	<!-- NAMES	-> GTAA/Namen (name) 	-->
	<xsl:template match="bg:names">
		<xsl:for-each select="bg:name">
			<nisv:hasEntityInRole>
				<nisv:EntityInRole>
					<nisv:hasOrganisation>
						<nisv:Organisation>
							<skos:prefLabel>
								<xsl:attribute name="xml:lang">nl</xsl:attribute>
							 	<xsl:value-of select="."/>
							</skos:prefLabel>
						</nisv:Organisation>
					</nisv:hasOrganisation>
				</nisv:EntityInRole>
			</nisv:hasEntityInRole>
		</xsl:for-each>
	</xsl:template>	

	<!-- PERSONNAMES	 -> GTAA/Persoonsnamen (personname) -->
	<xsl:template match="bg:personnames">
		<xsl:for-each select="bg:personname">
			<nisv:hasEntityInRole>
				<nisv:EntityInRole>
					<nisv:hasPerson>
						<nisv:Person>
							<skos:prefLabel>
								<xsl:attribute name="xml:lang">nl</xsl:attribute>
							 	<xsl:value-of select="."/>
							</skos:prefLabel>
						</nisv:Person>
					</nisv:hasPerson>
				</nisv:EntityInRole>
			</nisv:hasEntityInRole>
		</xsl:for-each>
	</xsl:template>	
		
	<!-- CAST 	-> persoon (name, character, clarification) -->
	<xsl:template match="bg:cast">
			<nisv:hasCast>
				<nisv:Cast>
					<nisv:hasPerson>
						<nisv:Person>
							<skos:prefLabel>
								<xsl:attribute name="xml:lang">nl</xsl:attribute>
								<xsl:value-of select="bg:name"/>
							</skos:prefLabel>
						</nisv:Person>
					</nisv:hasPerson>
					<xsl:if test="bg:character">
						<nisv:hasCharacter>
							<xsl:value-of select="bg:character"/>
						</nisv:hasCharacter>
					</xsl:if>
					<xsl:if test="bg:clarification">
						<nisv:hasClarification>
							<xsl:value-of select="bg:clarification"/>
						</nisv:hasClarification>
					</xsl:if>
				</nisv:Cast>
			</nisv:hasCast>
	</xsl:template>

	<!-- SPEAKER 	-> person (name,role) -->
	<xsl:template match="bg:speaker">
			<nisv:hasSpeaker>
				<nisv:Speaker>
					<nisv:hasPerson>
						<nisv:Person>
							<skos:prefLabel>
								<xsl:attribute name="xml:lang">nl</xsl:attribute>
							 	<xsl:value-of select="bg:name"/>
							</skos:prefLabel>
						</nisv:Person>
					</nisv:hasPerson>
					<xsl:if test="bg:role">
						<nisv:hasRole>
							<xsl:value-of select="bg:role"/>
						</nisv:hasRole>
					</xsl:if>
				</nisv:Speaker>
			</nisv:hasSpeaker>
	</xsl:template>

	<!-- PRODUCER	-> bedrijf (name)-->
	<xsl:template match="bg:producer">
		<nisv:hasProducer>
			<nisv:Producer>
				<nisv:hasOrganisation>
					<nisv:Organisation>
						<skos:prefLabel>
							<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 	<xsl:value-of select="bg:name"/>
						</skos:prefLabel>
					</nisv:Organisation>
				</nisv:hasOrganisation>
			</nisv:Producer>
		</nisv:hasProducer>
	</xsl:template>	

	<!-- SPONSOR 	 -> bedrijf	(name)	-->
	<xsl:template match="bg:sponsor">
		<nisv:hasSponsor>
			<nisv:Sponsor>
				<nisv:hasOrganisation>
					<nisv:Organisation>
						<skos:prefLabel>
							<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 	<xsl:value-of select="bg:name"/>
						</skos:prefLabel>
					</nisv:Organisation>
				</nisv:hasOrganisation>
			</nisv:Sponsor>
		</nisv:hasSponsor>
	</xsl:template>
	
	<!-- FUNDER		-> bedrijf (name)-->
	<xsl:template match="bg:funder">
		<nisv:hasFunder>
			<nisv:Funder>
				<nisv:hasOrganisation>
					<nisv:Organisation>
						<skos:prefLabel>
							<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 	<xsl:value-of select="bg:name"/>
						</skos:prefLabel>
					</nisv:Organisation>
				</nisv:hasOrganisation>
			</nisv:Funder>
		</nisv:hasFunder>
	</xsl:template>

	<!-- CONTRACTOR -> bedrijf	(name)-->
	<xsl:template match="bg:contractor">
		<nisv:hasContractor>
			<nisv:Contractor>
				<skos:prefLabel>
					<xsl:attribute name="xml:lang">nl</xsl:attribute>
				 	<xsl:value-of select="bg:name"/>
				</skos:prefLabel>
			</nisv:Contractor>
		</nisv:hasContractor>
	</xsl:template>
	
	<!--  EXECUTIVES	->	 bedrijf/persoon (name, role, clarification)
	-->
	<xsl:template match="bg:executive">
		<nisv:hasExecutive>
			<nisv:EntityInRole>
				<nisv:hasEntity>
					<nisv:ActingEntity>
						<skos:prefLabel>
							<xsl:attribute name="xml:lang">nl</xsl:attribute>
					 		<xsl:value-of select="bg:name"/>
						</skos:prefLabel>
					</nisv:ActingEntity>
				</nisv:hasEntity>
				<xsl:if test="bg:role">
					<nisv:hasRole>
						<xsl:value-of select="bg:role"/>
					</nisv:hasRole>
				</xsl:if>
				<xsl:if test="bg:clarification">
					<nisv:hasClarification>
						<xsl:value-of select="bg:clarification"/>
					</nisv:hasClarification>
				</xsl:if>
			</nisv:EntityInRole>
		</nisv:hasExecutive>
	</xsl:template>	
	
	<!-- CREATOR AND ORIGINALCREATOR	-> persoon (name, role, clarification, roles)
	-->
 	<xsl:template match="bg:creator">
 		<xsl:variable name="creatorName" select="bg:name"/>		

		<xsl:choose>
		
	 		<!-- For each roles/role a different Creator (same name)-->
			<xsl:when test="count(bg:roles/bg:role)">
				<xsl:for-each select="bg:roles/bg:role">
					<nisv:hasCreator>
						<nisv:Creator>
							<nisv:hasPerson>
								<nisv:Person>
									<skos:prefLabel>
										<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 				<xsl:value-of select="$creatorName"/>
									</skos:prefLabel>
								</nisv:Person>
							</nisv:hasPerson>
							<xsl:if test="self::node()[text()] != ''">
								<nisv:hasRole>
									<xsl:value-of select="."/>
								</nisv:hasRole>
							</xsl:if>
						</nisv:Creator>
					</nisv:hasCreator>
				</xsl:for-each>
			</xsl:when>

			<!-- For each role a different Creator (same name) -->
			<xsl:when test="count(bg:role)">
				<xsl:for-each select="bg:role">
					<nisv:hasCreator>
						<nisv:Creator>
							<nisv:hasPerson>
								<nisv:Person>
									<skos:prefLabel>
										<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 				<xsl:value-of select="$creatorName"/>
									</skos:prefLabel>
								</nisv:Person>
							</nisv:hasPerson>
							<xsl:if test="self::node()[text()] != ''">
								<nisv:hasRole>
									<xsl:value-of select="."/>
								</nisv:hasRole>
							</xsl:if>
						</nisv:Creator>
					</nisv:hasCreator>
				</xsl:for-each>
			</xsl:when>
			
			<!-- No role, so only a creator with name -->
			<xsl:when test="(count(bg:role) + count(bg:roles/bg:role)) = 0">
				<nisv:hasCreator>
					<nisv:Creator>
						<nisv:hasPerson>
							<nisv:Person>
								<skos:prefLabel>
									<xsl:attribute name="xml:lang">nl</xsl:attribute>
									<xsl:value-of select="$creatorName"/>
								</skos:prefLabel>
							</nisv:Person>
						</nisv:hasPerson>
					</nisv:Creator>
				</nisv:hasCreator>
			</xsl:when>

		</xsl:choose>
	</xsl:template>	

 	<xsl:template match="bg:originalCreator">
 		<xsl:variable name="creatorName" select="bg:name"/>

		<xsl:choose>

	 		<!-- For each roles/role a different Creator (same name)-->
			<xsl:when test="count(bg:roles/bg:role)">
				<xsl:for-each select="bg:roles/bg:role">
					<nisv:hasOriginalCreator>
						<nisv:OriginalCreator>
							<nisv:hasPerson>
								<nisv:Person>
									<skos:prefLabel>
										<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 				<xsl:value-of select="$creatorName"/>
									</skos:prefLabel>
								</nisv:Person>
							</nisv:hasPerson>
							<xsl:if test="self::node()[text()] != ''">
								<nisv:hasRole>
									<xsl:value-of select="."/>
								</nisv:hasRole>
							</xsl:if>
						</nisv:OriginalCreator>
					</nisv:hasOriginalCreator>
				</xsl:for-each>
			</xsl:when>

			<!-- For each role a different Creator (same name) -->
			<xsl:when test="count(bg:role)">
				<xsl:for-each select="bg:role">
					<nisv:hasOriginalCreator>
						<nisv:OriginalCreator>
							<nisv:hasPerson>
								<nisv:Person>
									<skos:prefLabel>
										<xsl:attribute name="xml:lang">nl</xsl:attribute>
						 				<xsl:value-of select="$creatorName"/>
									</skos:prefLabel>
								</nisv:Person>
							</nisv:hasPerson>
							<xsl:if test="self::node()[text()] != ''">
								<nisv:hasRole>
									<xsl:value-of select="."/>
								</nisv:hasRole>
							</xsl:if>
						</nisv:OriginalCreator>
					</nisv:hasOriginalCreator>
				</xsl:for-each>
			</xsl:when>

			<!-- No role, so only a creator with name -->
			<xsl:when test="(count(bg:role) + count(bg:roles/bg:role)) = 0">
				<nisv:hasOriginalCreator>
					<nisv:OriginalCreator>
						<nisv:hasPerson>
							<nisv:Person>
								<skos:prefLabel>
									<xsl:attribute name="xml:lang">nl</xsl:attribute>
									<xsl:value-of select="$creatorName"/>
								</skos:prefLabel>
							</nisv:Person>
						</nisv:hasPerson>
					</nisv:OriginalCreator>
				</nisv:hasOriginalCreator>
			</xsl:when>

		</xsl:choose>
	</xsl:template>

	<!-- END ORIGINALCREATOR -->

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
	
	<xsl:template match="bg:language">
		<xsl:choose >
			<!-- Test for a sub element named bg:language -->
			<xsl:when test="bg:language">
				<nisv:hasLanguage>
					<nisv:Language>
					  	<xsl:apply-templates />
					</nisv:Language>
				</nisv:hasLanguage>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="nisv:{local-name()}">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="bg:context">
		<nisv:hasContext>
			<nisv:Context>
				<xsl:for-each select="./*">
					<xsl:element name="nisv:{local-name()}">
						<xsl:value-of select="."/>
					</xsl:element>
				</xsl:for-each>
			</nisv:Context>
		</nisv:hasContext>
	</xsl:template>
	
	<!-- GEOGRAPHICAL CONCEPTS -->
	<xsl:template match="bg:productioncountries">
		<xsl:for-each select="bg:country">
			<nisv:hasProductionCountry>
				<nisv:Location>
					<skos:prefLabel>
						<xsl:attribute name="xml:lang">nl</xsl:attribute>
						<xsl:value-of select="."/>
					</skos:prefLabel>
				</nisv:Location>
			</nisv:hasProductionCountry>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="bg:locations">
		<xsl:for-each select="bg:location">
			<nisv:hasLocation>
				<nisv:Location>
					<skos:prefLabel>
						<xsl:attribute name="xml:lang">nl</xsl:attribute>
						<xsl:value-of select="."/>
					</skos:prefLabel>
				</nisv:Location>
			</nisv:hasLocation>
		</xsl:for-each>
	</xsl:template>
	
	<!-- Geographical, but not a SKOS concept -->
	<xsl:template match="bg:recordinglocations">
		<xsl:for-each select="bg:location">
			<nisv:hasRecordingLocation>
				<xsl:value-of select="."/>
			</nisv:hasRecordingLocation>
		</xsl:for-each>
	</xsl:template>
	
	<!-- OTHER SKOS CONCEPTS -->
	<xsl:template match="bg:genres">
		<xsl:for-each select="bg:genre">
			<nisv:hasGenre>
				<nisv:Genre>
					<skos:prefLabel>
						<xsl:attribute name="xml:lang">nl</xsl:attribute>
						<xsl:value-of select="."/>
					</skos:prefLabel>
				</nisv:Genre>
			</nisv:hasGenre>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template match="bg:keywords">
		<xsl:for-each select="bg:keyword">
			<nisv:hasSubject>
				<nisv:Subject>
					<skos:prefLabel>
						<xsl:attribute name="xml:lang">nl</xsl:attribute>
						<xsl:value-of select="."/>
					</skos:prefLabel>
				</nisv:Subject>
			</nisv:hasSubject>
		</xsl:for-each>
	</xsl:template>
	 
	<!--  EXPIRED CONCEPT SCHEME. NOT A SKOS CONCEPT-->
	<xsl:template match="bg:deprecatedkeyword">
		<xsl:for-each select="bg:keyword">
			<nisv:hasDeprecatedKeyword>
				<xsl:value-of select="."/>
			</nisv:hasDeprecatedKeyword>
		</xsl:for-each>
	</xsl:template>

	 
	<!--  For now, do not include transcripts.  -->
	<xsl:template match="bg:transcripts"/>
	
	<!-- A generic template to remove all elements that are only there to support sequences in XML. 
		For matching pattern see: Eg. https://stackoverflow.com/questions/1007018/xslt-expression-to-check-if-variable-belongs-to-set-of-elements
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
		<xsl:choose> 
			<!--  DATE TYPE ELEMENTS -->
			<xsl:when test="local-name() = 'creationdate'">
				<xsl:element name="nisv:hasCreationDate">
					<xsl:value-of select="."/>
				</xsl:element>			
			</xsl:when>

			<xsl:when test="local-name() = 'startdate'">
				<xsl:element name="nisv:hasStartDate">
					<xsl:value-of select="."/>
				</xsl:element>			
			</xsl:when>

			<xsl:when test="local-name() = 'enddate'">
				<xsl:element name="nisv:hasEndDate">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>

			<xsl:when test="local-name() = 'montagedate'">
				<xsl:element name="nisv:hasMontageDate">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>

			<xsl:when test="local-name() = 'datereceived'">
				<xsl:element name="nisv:hasDateReceived">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'sortdate'">
				<xsl:element name="nisv:hasSortDate">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<!--  TIME TYPE ELEMENTS -->
			<xsl:when test="local-name() = 'starttime'">
				<xsl:element name="nisv:hasStartTime">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>

			<xsl:when test="local-name() = 'endtime'">
				<xsl:element name="nisv:hasEndTime">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
						
			<xsl:when test="local-name() = 'starttimestamp'">
				<xsl:element name="nisv:hasStartTimestamp">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<!-- CARRIER TYPE ELEMENTS -->	
			<xsl:when test="local-name() = 'location'">
				<xsl:element name="nisv:hasCarrierLocation">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'carrierreference'">
				<xsl:element name="nisv:hasCarrierReference">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'carriertype'">
				<xsl:element name="nisv:hasCarrierType">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'carrierclass'">
				<xsl:element name="nisv:hasCarrierClass">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'startoncarrier'">
				<xsl:element name="nisv:hasCarrierStartPosition">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'endoncarrier'">
				<xsl:element name="nisv:hasCarrierEndPosition">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<xsl:when test="local-name() = 'carrierid'">
				<xsl:element name="nisv:hasCarrierId">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<!-- LOCATION TYPE ELEMENTS -->	
			<xsl:when test="local-name() = 'location'">
				<xsl:element name="nisv:hasCarrierLocation">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:when>
			
			<!-- OTHER TYPE LEAVE NODES -->
			<xsl:otherwise>
				<xsl:element name="nisv:{local-name()}">
					<xsl:value-of select="."/>
				</xsl:element>
			</xsl:otherwise>

		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="text()"/>

</xsl:transform>
