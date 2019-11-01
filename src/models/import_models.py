from enum import Enum, unique #https://docs.python.org/3.5/library/enum.html
import models.import_schema as schema
from rdflib.namespace import RDF, SKOS
from rdflib.term import URIRef, Literal, BNode


"""Contains models for the DAAN data, and functions for converting it to RDF"""

""" -------------- ENUMS FOR STRONG TYPING --------------- """

@unique
class ObjectType(Enum):  # models object/record types in DAAN
	SERIES = 'SERIES'
	SEASON = 'SEASON'
	PROGRAM = 'PROGRAM'
	ITEM = 'ITEM'
	AGGREGATEASSET = 'AGGREGATEASSET'
	LOGTRACKITEM = 'LOGTRACKITEM'

@unique
class LogTrackType(Enum):  # models the logtrack types in DAAN
	#as described in the documentation
	SCENE_DESC = 'scenedesc'
	TECHNICAL = 'Technical'
	SUBTITLES = 'Subtitles'
	FACE_LABELS = 'Face Labels'
	BATON_REMARKS = 'Baton remarks (compliance/auto)' #this one is not valid?
	SPEAKER_LABELS = 'Speaker Labels'
	ACTIONS = 'Actions'
	EXTRACTED_LABELS = 'Extracted Labels'
	SPEECH_TRANSCRIPT = 'Transcripted Speech'

	#found after importing
	AGENDA_POINT = 'Agenda Point'
	BATON_ERRORS = 'Baton errors (compliance/auto)'
	BATON_REMARKS2 = 'Baton remarks (compliance|auto)'
	SUBTITLES_C890 = 'Subtitles (Cavena 890)'
	STORY = 'Story'
	COMPOSITION = 'Composition'
	EXTRACTED_DATA = 'Extracted Data'
	SCENE_DESC2 = 'Scenedesc'
	SCENE_DESC3 = 'Scene description'
	SCENE_DESC4 = 'Scene Desc Logtrack'
	MY_SCENES = 'My Scenes'
	MARKUS = 'Markus testing GMI logtracks'
	PROGRAMSITEID = 'ProgramSiteID'
	STUDIO_PLAYER = 'Studio Player Log Entry'
	TECHNICAL2 = 'Technical Logtrack'
	TECHNICAL3 = 'technical'

	#fall back type
	UNKNOWN = 'unknown'

# some important DAAN field names
DAAN_PARENT = "parents"
DAAN_PARENT_ID = "parent_id"
DAAN_PARENT_TYPE = "parent_type"
DAAN_PROGRAM_ID = "program_ref_id"
DAAN_PAYLOAD = "payload"

""" -------------- MODEL HELPER FUNCTION --------------- """


def isSceneDescription(logtrackType):
	"""Checks if the logtrack type indicates it is a Scene Description"""
	return logtrackType == LogTrackType.SCENE_DESC.value or logtrackType == LogTrackType.SCENE_DESC2.value or logtrackType == LogTrackType.SCENE_DESC3.value or logtrackType == LogTrackType.SCENE_DESC4.value


def getMetadataValue(metadata, metadataField):
	"""Gets the value of the metadata field from the JSON metadata.
	Returns either a single value, or a list of multiple values"""

	if "," in metadataField:
		fieldParts = metadataField.split(",")

		if type(metadata) is not list:
			valueList = [metadata]  # create a list as the metadata field could contain a list at some point
		else:
			valueList = metadata

		for part in fieldParts:
			part = part.strip()  # remove any whitespace
			newValueList = []
			found = False
			for value in valueList:
				if value:
					if part in value:
						found = True
						if type(value[part]) is list:
							newValueList.extend(value[part])
						else:
							newValueList.append(value[part])
			if not found:
				return ""  # no value for the metadata field
			valueList = newValueList

		return valueList
	else:
		if metadataField in metadata:
			return metadata[metadataField]
		else:
			return ""


def payloadToRdf(payload, parentNode, classUri, classes, graph):
	"""Converts the metadata described in payload (json) to RDF, and attaches it to the parentNode
	(e.g. the parentNode can be the identifier node for a program, and the payload the metadata describing
	that program.). Calls itself recursively to handle any classes in the metadata, e.g. the publication
	belonging to a program.
	Uses the classUri of the parent node to select the right information from  classes for the conversion.
	Returns the result in graph"""

	# Select the relevant properties for this type of parent using the classUri
	properties = classes[classUri]["properties"]

	# retrieve metadata for each relevant property
	for uri, property in properties.items():

		# try each possible path for the property until find some metadata
		for path in property["paths"]:
			newPayload = getMetadataValue(payload, path)
			usedPath = path
			if newPayload:
				break

		# if we found metadata for this property
		if newPayload:
			if type(newPayload) is not list:
				newPayload = [newPayload]  # we can have a list of metadata, so make sure it is always
				# a list for consistent handling

			# for each item in the metadata list
			for newPayloadItem in newPayload:
				# if range of property is simple data type, just link it to the parent using the property
				if property["range"] in schema.XSD_TYPES:
					graph.add((parentNode, URIRef(uri), Literal(newPayloadItem, datatype=property["range"]))) # add the new payload as the value
				elif property["rangeSuperClass"] == schema.ACTING_ENTITY or property["rangeSuperClass"] == str(SKOS.Concept):
					# In these cases, we have a class as range, but only a simple value in DAAN, as we want to model a label
					#  from DAAN with a skos:Concept in the RDF
					# create a node for the skos concept

					# look one step higher to be able to get to the ID of a thesaurus item
					if "," in usedPath:
						classPath = ",".join(usedPath.split(",")[:-1])
						conceptMetadata = getMetadataValue(payload, classPath)

						# the value could be a list, so make sure it always is so can treat everything the same way
						if type(conceptMetadata) is not list:
							conceptMetadata = [conceptMetadata]

					conceptNode = None
					for concept in conceptMetadata:
						if "origin" in concept and "value" in concept and "resolved_value" in concept:
							if concept["resolved_value"] == newPayloadItem:
								# we have a thesaurus concept and can use the value to generate the URI
								if property["range"] in schema.NON_GTAA_TYPES:
									conceptNode = URIRef(schema.NON_GTAA_NAMESPACE + concept["value"])
								else:
									conceptNode = URIRef(schema.GTAA_NAMESPACE + concept["value"])

					if not conceptNode:
						# we only have a label, so we create a blank node
						conceptNode = BNode()

					graph.add((conceptNode, RDF.type, URIRef(property["range"])))
					graph.add((parentNode, URIRef(uri), conceptNode))  # link it to the parent

					# and set the pref label of the concept node to be the DAAN payload item
					graph.add((conceptNode, SKOS.prefLabel, Literal(newPayloadItem, lang="nl")))
				else:
					# we have a class as range
					# create a blank node for the class ID, and a triple to set the type of the class
					blankNode = BNode()
					graph.add((blankNode, RDF.type, URIRef(property["range"])))
					graph.add((parentNode, URIRef(uri), blankNode))  # link it to the parent
					# and call the function again to handle the properties for the class
					payloadToRdf(newPayloadItem, blankNode, property["range"], classes, graph )

	return


def parentToRdf(metadata, childNode, childType, graph):
	"""Depending on the type of the child (e.g. program) retrieve the information about its
	parents from the metadata, link the child to the parents, and return the new instances and
	properties in the graph"""
	if childType == schema.CLIP:  # for a clip, use the program reference
		graph.add((childNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + metadata[DAAN_PROGRAM_ID])))
	elif DAAN_PARENT in metadata and metadata[DAAN_PARENT] and DAAN_PARENT in metadata[DAAN_PARENT]:
		# for other
		if type(metadata[DAAN_PARENT][DAAN_PARENT]) is list:
			parents = metadata[DAAN_PARENT][DAAN_PARENT]
		else:  # convert it to a list for consistent handling
			parents = [metadata[DAAN_PARENT][DAAN_PARENT]]

		for parent in parents:
			# for each parent, link it with the correct relationship given the types
			if childType == schema.CARRIER:  # link carriers as children
				graph.add((URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID]), URIRef(schema.HAS_CARRIER), childNode))
			elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
				graph.add((childNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID])))
			elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
				graph.add((childNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID])))
			elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
				graph.add((childNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID])))

	return

