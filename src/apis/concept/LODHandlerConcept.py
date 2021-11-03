from rdflib import Graph
from rdflib.plugin import PluginException
from util.APIUtil import APIUtil
from urllib.error import URLError


class LODHandlerConcept(object):
	""" OpenSKOS platform provides RDF data for each SKOS concept. As far as I know the
		sub domain data.beeldengeluid.nl is forwarded to OpenSKOS platform on DNS level.

		Paths after the domain name are forwarded to OpenSKOS:
			http://data.beeldengeluid.nl/<set>/<notation>, where <set>/<notation> is to be filled
			with, for example: 'gtaa' and '58027'.

		... and by adding an '.rdf' extension the RDF/XML is also available:
			http://data.beeldengeluid.nl/gtaa/58027.rdf

		Note: this is not really a proper LOD practice. To fix that this class makes the concept
		dereferenceable on the data.rdlabs.beeldengeluid.nl sub domain with <set> and <notation>
		paths:
			http://data.rdlabs.beeldengeluid.nl/gtaa/58027
		e.g.: `curl -X GET "http://localhost:5309/concept/gtaa/27948" -H "accept: application/json"`

		The LOD server enables content negotiation, making it possible to get the data serialization
		in any format that RDFlib can handle, e.g. RDF/XML, Turtle, N3, JSON-LD.
		HTML is not yet supported.
	"""
	def __init__(self, config):
		self.config = config

	@staticmethod
	def get_concept_uri(set_spec, notation):
		uri = u'http://data.beeldengeluid.nl/%s/%s.rdf' % (set_spec, notation)
		return uri

	@staticmethod
	def get_concept_data(uri, return_format=None):
		graph = Graph()
		try:
			# uri = 'http://www.w3.org/People/Berners-Lee/card'
			# TODO: fix this issue in rdflib: https://github.com/RDFLib/rdflib/issues/1430
			graph.parse(location=uri, format='xml')  # Note that OpenSKOS can only return RDF+XML
		except URLError as e:
			return None
		except FileNotFoundError as e:
			print(f'{str(e)}')
			return None

		try:
			return graph.serialize(format=return_format)
		except PluginException as e:
			return None

	def get_concept_rdf(self, set_spec, notation, return_format):
		uri = self.get_concept_uri(set_spec, notation)
		data = self.get_concept_data(uri, return_format)
		if data:
			return APIUtil.toSuccessResponse(data)
		return APIUtil.toErrorResponse('bad_request', 'Invalid concept URI or return format')
