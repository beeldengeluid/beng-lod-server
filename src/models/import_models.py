from enum import Enum, unique #https://docs.python.org/3.5/library/enum.html
import models.import_schema as schema
from abc import abstractmethod
from rdflib.namespace import RDF, SKOS
from rdflib.term import URIRef, Literal, BNode
import json
import copy

""" -------------- ENUMS FOR STRONG TYPING --------------- """

@unique
class ObjectType(Enum):
	SERIES = 'SERIES'
	SEASON = 'SEASON'
	PROGRAM = 'PROGRAM'
	ITEM = 'ITEM'
	AGGREGATEASSET = 'AGGREGATEASSET'
	LOGTRACKITEM = 'LOGTRACKITEM'

	def toESField(self):
		if self.name in ['SERIES', 'SEASON', 'PROGRAM']:
			return self.name.lower()
		elif self.name == 'ITEM':
			return 'assetItems'
		elif self.name == 'AGGREGATEASSET':
			return 'aggregateAsset'
		elif self.name == 'LOGTRACKITEM':
			return 'logTrackItems'
		return None

@unique
class LogTrackType(Enum):
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

#these contain a LOT of data, so better store them separately for now
BULKY_LOGTRACKS = [] # LogTrackType.SUBTITLES, LogTrackType.SPEECH_TRANSCRIPT


DAAN_PARENT = "parents"
DAAN_PARENT_ID = "parent_id"
DAAN_PARENT_TYPE = "parent_type"
DAAN_PROGRAM_ID = "program_ref_id"
DAAN_PAYLOAD = "payload"

""" -------------- MODEL HELPER FUNCTION --------------- """

def isSceneDescription(logtrackType):
	return logtrackType == LogTrackType.SCENE_DESC.value or logtrackType == LogTrackType.SCENE_DESC2.value or logtrackType == LogTrackType.SCENE_DESC3.value or logtrackType == LogTrackType.SCENE_DESC4.value

def getMetadataValue(metadata, metadataField):
	"""Gets the value of the metadata field from the JSON metadata for a search result.
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

	properties = classes[classUri]["properties"]

	for uri, property in properties.items():

		for path in property["paths"]:
			newPayload = getMetadataValue(payload, path)
			usedPath = path
			if newPayload:
				break

		if newPayload:
			if type(newPayload) is not list:
				newPayload = [newPayload]

			for newPayloadItem in newPayload:
				# if range of property is simple data type
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
	# handle partOf relations - need to be done separately as the relation depends on the parent and/or child type
	if childType == schema.CLIP:
		graph.add((childNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + metadata[DAAN_PROGRAM_ID])))
	elif DAAN_PARENT in metadata and metadata[DAAN_PARENT] and DAAN_PARENT in metadata[DAAN_PARENT]:
		if type(metadata[DAAN_PARENT][DAAN_PARENT]) == list:
			for parent in metadata[DAAN_PARENT][DAAN_PARENT]:
				if childType == schema.CARRIER:
					graph.add((URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID]), URIRef(schema.HAS_CARRIER), childNode))
				elif parent[DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
					graph.add((childNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID])))
				elif parent[DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
					graph.add((childNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID])))
				elif parent[DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
					graph.add((childNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + parent[DAAN_PARENT_ID])))
		else:
			if childType == schema.CARRIER:
				graph.add((URIRef(schema.NISV_NAMESPACE + metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_ID]), URIRef(schema.HAS_CARRIER), childNode))
			elif metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_TYPE] == ObjectType.SERIES.name:
				graph.add((childNode, URIRef(schema.IS_PART_OF_SERIES), URIRef(schema.NISV_NAMESPACE + metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_ID])))
			elif metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_TYPE] == ObjectType.SEASON.name:
				graph.add((childNode, URIRef(schema.IS_PART_OF_SEASON), URIRef(schema.NISV_NAMESPACE + metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_ID])))
			elif metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_TYPE] == ObjectType.PROGRAM.name:
				graph.add((childNode, URIRef(schema.IS_PART_OF_PROGRAM), URIRef(schema.NISV_NAMESPACE + metadata[DAAN_PARENT][DAAN_PARENT][DAAN_PARENT_ID])))

	return


""" -------------- X-OMGEVING OBJECT MODEL --------------- """

#Abstract class subclassed by Series, Season, Program, AssetItem, AggregateAsset, etc...
#This class represents a thing that is part of the eventually created Aggregation object
class AggregateObject():

	def __init__(self, payload):
		# when loading from DAAN the payload is in payload['payload'] otherwise when loading from the aggregate index, the payload is already fine
		self.payload = payload['payload'] if 'payload' in payload else payload

		# default fields present for every aggregate object
		self.id = payload['id'] if 'id' in payload else None  # it's None for Segments
		self.date_created = payload['date_created'] if 'date_created' in payload else None # creation date in DAAN
		self.date_last_updated = payload['date_last_updated'] if 'date_last_updated' in payload else None # last updated in DAAN
		self.site_id = payload['site_id'] if 'site_id' in payload else None  # defines an unique, platform independent ID (FIXME sometimes null for logtracks)

		# parents
		self.parents = self.getParents(payload)

		# if the payload is loaded from the aggregate store, this will do nothing, but prevent running this anyway
		if 'payload' in payload:
			self.removeUselessFields() #FIXME parents are not removed from aggregate asset...

	def getParents(self, payload):
		parents = []
		if DAAN_PARENT in payload:
			for parent in payload[DAAN_PARENT]:
				if DAAN_PARENT_ID in parent and DAAN_PARENT_TYPE in parent:
					parents.append((parent[DAAN_PARENT_ID], parent[DAAN_PARENT_TYPE]))
		return parents

	def removeUselessFields(self):
		if 'acl_hash' in self.payload: del self.payload['acl_hash'] # B&G internal: hash of aclGroups (see next)
		if 'aclGroups' in self.payload: del self.payload['aclGroups'] # B&G internal: authorizations per publishing point
		if 'payload_model' in self.payload: del self.payload['payload_model'] # B&G internal: URL pointing to the payload model
		for k in copy.deepcopy(self.payload).keys(): # B&G internal: OMP specific fields
			if k.find('omp.') != -1:
				del self.payload[k]

	@property
	def classUri(self):
		return ""

	def toRdf(self, graphHandler):
		"""Converts the object to a list of RDF triples describing it"""
		graph = graphHandler.getGraph()
		objectNode = URIRef(schema.NISV_NAMESPACE + self.id)
		graph.add((objectNode, RDF.type, URIRef(self.classUri)))
		payloadToRdf(self.payload, objectNode, self.classUri, graphHandler.classes, graph)
		parentToRdf(self.parents, objectNode, self.classUri, graph)

		return graph

	def __str__(self):
		return json.dumps(self.toIndexObject(), indent=4, sort_keys=True)


class Series(AggregateObject):

	def __init__(self, payload):
		super().__init__(payload)

	@property
	def classUri(self):
		return schema.SERIES

	def removeUselessFields(self):
		super().removeUselessFields()
		if 'nisv.metadatastatus' in self.payload: del self.payload['nisv.metadatastatus'] # B&G internal: TODO

class Season(AggregateObject):

	def __init__(self, payload):
		super().__init__(payload)

	@property
	def classUri(self):
		return schema.SEASON

class Program(AggregateObject):

	def __init__(self, payload):
		super().__init__(payload)

	@property
	def classUri(self):
		return schema.PROGRAM

	#task IDs wel weer erbij zetten
	def removeUselessFields(self):
		super().removeUselessFields()
		if 'nisv.sourcedescription' in self.payload: del self.payload['nisv.sourcedescription'] # XML used to generate metadata
		if 'nisv.sourcedescription2' in self.payload: del self.payload['nisv.sourcedescription2'] # XML used to generate metadata
		#if 'nisv.tasklist' in self.payload: del self.payload['nisv.tasklist'] # B&G internal: describing things to do for the metadata
		if 'nisv.publishings' in self.payload: del self.payload['nisv.publishings'] # B&G internal: which portals the program is published on
		if 'nisv.tenant' in self.payload: del self.payload['nisv.tenant'] # B&G internal: what DAAN tenant the program comes from
		if 'nisv.mdissues' in self.payload: del self.payload['nisv.mdissues'] # B&G internal: issues with metadata?
		if 'nisv.seriestitle' in self.payload: del self.payload['nisv.seriestitle']
		if 'nisv.seasontitle' in self.payload: del self.payload['nisv.seasontitle']

# TODO: implement Segment and AggregateAsset handling
# class Segment(AggregateObject):
#
# 	def __init__(self, payload):
# 		super().__init__(payload)
#
# class AggregateAsset(AggregateObject):
#
# 	def __init__(self, payload):
# 		super().__init__(payload)
# 		self.segments = [Segment(s) for s in payload['segments']] if 'segments' in payload and payload['segments'] else None
#
# 	def removeUselessFields(self):
# 		if 'itemset.segmentlist' in self.payload: del self.payload['itemset.segmentlist']
#
# 	def toIndexObject(self):
# 		obj = super().toIndexObject()
# 		obj['segments'] = [s.toIndexObject() for s in self.segments] if self.segments else None
# 		return obj

class AssetItem(AggregateObject):

	def __init__(self, payload):
		super().__init__(payload)

	@property
	def classUri(self):
		return schema.CARRIER

	def removeUselessFields(self):
		super().removeUselessFields()
		if 'nisv.fastlaneimportsource' in self.payload: del self.payload['nisv.fastlaneimportsource']
		if 'nisv.fastlanebatonprofile' in self.payload: del self.payload['nisv.fastlanebatonprofile']
		if 'asset.qcStatus' in self.payload: del self.payload['asset.qcStatus']
		if 'asset.qcSeverity' in self.payload: del self.payload['asset.qcSeverity']
		#if 'nisv.carriertypeid' in self.payload: del self.payload['nisv.carriertypeid'] ZOU BIJ ELKE DRAGER MOETEN ZITTEN
		if 'nisv.tapegroup' in self.payload: del self.payload['nisv.tapegroup']
		if 'nisv.projectid' in self.payload: del self.payload['nisv.projectid']
		if 'nisv.projectids' in self.payload: del self.payload['nisv.projectids']
		if 'nisv.publications' in self.payload: del self.payload['nisv.publications'] # already available under publication in the PROGRAM part
		if 'nisv.programtitle' in self.payload: del self.payload['nisv.programtitle']
		if 'nisv.seriestitle' in self.payload: del self.payload['nisv.seriestitle']
		if 'nisv.seasontitle' in self.payload: del self.payload['nisv.seasontitle']

# TODO: create a model for logtracks other than scene descriptions (which are modelled as clips)
class LogTrackItem(AggregateObject):

	def __init__(self, payload):
		super().__init__(payload)
		logTrackType = None
		try:
			if 'logtrack_type' in payload:
				logTrackType = LogTrackType(payload['logtrack_type'])
			elif 'payload' in payload and 'logtrack_type' in payload['payload']:
				logTrackType = LogTrackType(payload['payload']['logtrack_type'])
			else:
				raise ValueError("No logtrack type")
		except ValueError as e:
			#logTrackType = LogTrackType('unknown')
			print('invalid logtrack type: %s' % payload['logtrack_type'])
		self.logtrack_type = logTrackType # see LogTrackType for possible values
		if 'media_start' in payload:
			self.media_start = payload['media_start'] # media start relative to start of file
		elif 'payload' in payload and 'media_start' in payload['payload']:
			self.media_start = payload['payload']['media_start'] # media start relative to start of file
		if 'media_duration' in payload:
			self.media_duration = payload['media_duration'] # media start relative to start of file
		elif 'payload' in payload and 'media_duration' in payload['payload']:
			self.media_duration = payload['payload']['media_duration'] # duration

	def removeUselessFields(self):
		if 'logtrackitem.siteid' in self.payload: del self.payload['logtrackitem.siteid'] # duplicate: same as site_id of LOGTRACKITEM
		if 'nisv.programid' in self.payload: del self.payload['nisv.programid'] # duplicate: same as site_id of PROGRAM
		if 'nisv.dragerkant' in self.payload: del self.payload['nisv.dragerkant'] # not needed to determine play pos
		if 'nisv.beginposdrager' in self.payload: del self.payload['nisv.beginposdrager'] # not needed to determine play pos


class Clip(LogTrackItem):

	@property
	def classUri(self):
		return schema.CLIP

	def getParents(self, payload):
		parents = []
		if DAAN_PROGRAM_ID in payload:
			parents.append((payload[DAAN_PROGRAM_ID], ))
		elif DAAN_PAYLOAD in payload and DAAN_PROGRAM_ID in payload[DAAN_PAYLOAD]:
			parents.append((payload[DAAN_PAYLOAD][DAAN_PROGRAM_ID], ""))
		return parents

