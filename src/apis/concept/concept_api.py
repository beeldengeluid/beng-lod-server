from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource
from apis.concept.LODHandlerConcept import LODHandlerConcept
from apis.api_util import accept_type_to_mime_type, ld_to_mimetype_map

api = Namespace('concept', description='Concepts in RDF for Netherlands Institute for Sound and Vision.')

@api.route('concept/<set_code>/<notation>', endpoint='concept')
class LODConceptAPI(Resource):
    LD_TO_MIME_TYPE = ld_to_mimetype_map()

    @api.response(404, 'Resource does not exist error')
    def get(self, set_code, notation):
        """ Get the RDF for the SKOS Concept. """
        accept_type = request.headers.get('Accept')
        user_format = request.args.get('format', None)
        mime_type = accept_type_to_mime_type(accept_type)

        # override the accept format if the user specifies a format
        if user_format and user_format in self.LD_TO_MIME_TYPE:
            mime_type = self.LD_TO_MIME_TYPE[user_format]

        resp, status_code, headers = LODHandlerConcept(current_app.config).get_concept_rdf(
            set_code,
            notation,
            mime_type.to_ld_format()
        )

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers