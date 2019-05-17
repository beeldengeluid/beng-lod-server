from rdflib import Graph
from util.APIUtil import APIUtil

#TODO this class is now just a copy of the LODHandler, implement it
class LODHandlerConcept(object):
	''' OpenSKOS platform provides RDF data for each concept. As far as I know the 
		subdomain data.beeldengeluid.nl is forwarded to openskos platform on DNS level. 
		
		For example the current concept resolving forwards to the Openskos that manages the paths
		after the domain name:
			http://data.beeldengeluid.nl/<set>/<notation>, where <set>/<notation> is to be filled 
			with, for example: 'gtaa' and '58027'.
			
		and by adding an extension the RDF/XML is also available:
			http://data.beeldengeluid.nl/gtaa/58027.rdf
			
		This class makes the concept dereferencable on the rdlabs subdomain with <set> and <notation>
		paths:
			http://data.rdlabs.beeldengeluid.nl/gtaa/58027
			e.g.: `curl -X GET "http://localhost:5309/concept/gtaa/27948" -H "accept: application/json"`
			
		In the future the data.beeldengeluid.nl domain will be under control of the LOD server. For
		that, a properly managed transition needs to be undertaken. 
		
		The LOD server enables content negotiation, making it possible to get the data serialization 
		in any format that RDFlib can handle, e.g. RDF/XML, Turtle, N3, JSON-LD and even.
	'''
	def __init__(self, config):
		self.config = config
	
	def getConceptRDF(self,set,notation,returnFormat):
		graph = Graph()
		uri = u'http://data.beeldengeluid.nl/%s/%s.rdf'%(set,notation)
		print 'Debug: ', uri
		graph.load( uri)
		data = graph.serialize(format=returnFormat)
		if data:
			return APIUtil.toSuccessResponse(data)
		return APIUtil.toErrorResponse('bad_request', 'That return format is not supported')
