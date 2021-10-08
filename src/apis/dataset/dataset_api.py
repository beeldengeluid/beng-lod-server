from flask import current_app, request, Response
from flask_restx import Namespace, fields, Resource
from apis.dataset.DataCatalogLODHandler import DataCatalogLODHandler
from urllib.parse import urlparse, urlunparse
from apis.mime_type_util import parse_accept_header, MimeType

api = Namespace('dataset', description='Datasets in RDF for Netherlands Institute for Sound and Vision.')

""" --------------------------- RESOURCE ENDPOINT -------------------------- """

def prepare_beng_uri(path):
    """ Use the domain and the path given to construct a proper Beeld en Geluid URI. """
    parts = urlparse(current_app.config['BENG_DATA_DOMAIN'])
    new_parts = (parts.scheme, parts.netloc, path, None, None, None)
    return urlunparse(new_parts)

@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/dataset/<number>', endpoint='datasets')
@api.doc(params={'number': {'description': 'Enter a zero padded 4 digit integer value.', 'in': 'number'}})
class LODDatasetAPI(Resource):
    """ Serve the RDF for the dataset in the format that was requested. A dataset contains distributions.
    """

    @api.response(404, 'Resource does not exist error')
    def get(self, number=None):
        """ Get the RDF for the Dataset, including its DataDownloads.
        All triples for the Dataset and its DataDownloads are included.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        dataset_uri = prepare_beng_uri(path=f'id/dataset/{number}')

        resp, status_code, headers = DataCatalogLODHandler(app_config=current_app.config).get_dataset(
            dataset_uri, mime_format=mime_type.to_ld_format()
        )

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers

@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/datacatalog/<number>', endpoint='data_catalogs')
@api.doc(params={'number': {'description': 'Enter a zero padded 3 digit integer value.', 'in': 'number'}})
class LODDataCatalogAPI(Resource):

    @api.response(404, 'Resource does not exist error')
    def get(self, number=None):
        """ Get the RDF for the DataCatalog, including its Datasets.
        All triples describing the DataCatalog and its Datasets are included.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        data_catalog_uri = prepare_beng_uri(path=f'id/datacatalog/{number}')

        resp, status_code, headers = DataCatalogLODHandler(
            app_config=current_app.config
        ).get_data_catalog(data_catalog_uri, mime_format=mime_type.to_ld_format())

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers

@api.doc(responses={
    200: 'Success',
    400: 'Bad request.',
    404: 'Resource does not exist.',
    406: 'Not Acceptable. The requested format in the Accept header is not supported by the server.'
})
@api.route('id/datadownload/<number>', endpoint='data_downloads')
@api.doc(params={'number': {'description': 'Enter a zero padded 4 digit integer value.', 'in': 'number'}})
class LODDataDownloadAPI(Resource):

    @api.response(404, 'Resource does not exist error')
    def get(self, number=None):
        """ Get the RDF for the DataDownload.
        """
        mime_type, accept_profile = parse_accept_header(request.headers.get('Accept'))
        data_download_uri = prepare_beng_uri(path=f'id/datadownload/{number}')

        resp, status_code, headers = DataCatalogLODHandler(
            app_config=current_app.config
        ).get_data_download(data_download_uri, mime_format=mime_type.to_ld_format())

        # make sure to apply the correct mimetype for valid responses
        if status_code == 200:
            return Response(resp, mimetype=mime_type.value, headers=headers)

        # otherwise resp SHOULD be a json error message and thus the response can be returned like this
        return resp, status_code, headers
