import json

from mockito import when

import util.ld_util

from apis.dataset.dataset_api import LODDataAPI


def test_init():
    lod_data_api = LODDataAPI()
    assert isinstance(lod_data_api, LODDataAPI)


def test___get_lod_view_resource(application, application_settings, i_dataset):
    DUMMY_URL = "http://data.beeldengeluid.nl/id/dataset/0001"
    lod_data_api = LODDataAPI()

    with application.test_request_context():  # need to work within the app context as _get_lod_view_gtaa() uses the render_template() van Flask

        with when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(i_dataset):
            html_result = lod_data_api._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )

        assert html_result
        graph_json = json.loads(i_dataset.serialize(format="json-ld"))
        for item in graph_json:
            assert str(item["@id"]) in html_result


def test___get_lod_view_resource_error(application, application_settings):
    DUMMY_URL = "http://data.beeldengeluid.nl/id/dataset/0001"
    lod_data_api = LODDataAPI()

    with application.test_request_context():  # need to work within the app context as _get_lod_view_gtaa() uses the render_template() van Flask

        with when(util.ld_util).get_lod_resource_from_rdf_store(
            DUMMY_URL,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(None):
            html_result = lod_data_api._get_lod_view_resource(
                DUMMY_URL,
                application_settings.get("SPARQL_ENDPOINT"),
                application_settings.get("URI_NISV_ORGANISATION"),
            )

        assert not html_result
