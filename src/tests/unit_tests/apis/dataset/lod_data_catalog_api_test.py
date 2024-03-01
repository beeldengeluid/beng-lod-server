import pytest

from mockito import when, verify, unstub

import util.ld_util
import apis.dataset.dataset_api
from models.DatasetApiUriLevel import DatasetApiUriLevel
from util.mime_type_util import MimeType


def test_init():
    lod_data_catalog_api = apis.dataset.dataset_api.LODDataCatalogAPI()
    assert isinstance(lod_data_catalog_api, apis.dataset.dataset_api.LODDataCatalogAPI)


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_200(mime_type, application_settings, generic_client, datacatalog_url):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URI = f"http://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_SERIALISATION = "just something pretending to be a serialisation of a graph"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI)._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_PAGE)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, mime_format=mime_type.to_ld_format()
        ).thenReturn(DUMMY_SERIALISATION)
        when(
            apis.dataset.dataset_api.DataCatalogLODHandler
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        ).thenReturn()

        resp = generic_client.get(
            "offline",
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 200

        if mime_type is MimeType.HTML:
            assert (
                DUMMY_PAGE in resp.text.decode()
            )  # client adds a newline at the end of the response for some reason
        else:
            assert resp.text.decode() == DUMMY_SERIALISATION

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        ).is_valid_data_catalog(DUMMY_URI)
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI,
            times=1 if mime_type is MimeType.HTML else 0,
        )._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler,
            times=1 if mime_type is not MimeType.HTML else 0,
        ).get_data_catalog(DUMMY_URI, mime_format=mime_type.to_ld_format())
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler,
            times=1 if mime_type is not MimeType.HTML else 0,
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        )

    finally:
        unstub()


def test_get_200_mime_type_None(application_settings, generic_client, datacatalog_url):
    """Tests the default behaviour for the mime type, which is currently to set it to JSON-LD if the input is None"""
    DUMMY_IDENTIFIER = 1234
    DUMMY_URI = f"http://{DUMMY_IDENTIFIER}"
    DUMMY_SERIALISATION = "just something pretending to be a serialisation of a graph"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    input_mime_type = None
    default_mimetype = MimeType.JSON_LD

    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI)._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_PAGE)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, mime_format=default_mimetype.to_ld_format()
        ).thenReturn(DUMMY_SERIALISATION)
        when(
            apis.dataset.dataset_api.DataCatalogLODHandler
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        ).thenReturn()

        resp = generic_client.get(
            "offline",
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": input_mime_type},
        )

        assert resp.status_code == 200

        if default_mimetype is MimeType.HTML:
            assert (
                DUMMY_PAGE in resp.text.decode()
            )  # client adds a newline at the end of the response for some reason
        else:
            assert resp.text.decode() == DUMMY_SERIALISATION

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        ).is_valid_data_catalog(DUMMY_URI)
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI,
            times=1 if default_mimetype is MimeType.HTML else 0,
        )._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler,
            times=1 if default_mimetype is not MimeType.HTML else 0,
        ).get_data_catalog(DUMMY_URI, mime_format=default_mimetype.to_ld_format())
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler,
            times=1 if default_mimetype is not MimeType.HTML else 0,
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        )

    finally:
        unstub()


@pytest.mark.parametrize(
    "mime_type, error_cause",
    [
        (MimeType.HTML, "invalid_datacatalog"),
        (MimeType.JSON_LD, "invalid_datacatalog"),
        (MimeType.JSON_LD, "serialisation_failed"),
    ],
)
def test_get_400(
    mime_type,
    error_cause,
    application_settings,
    generic_client,
    datacatalog_url,
    caplog,
):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URI = f"http://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_SERIALISATION = "just something pretending to be a serialisation of a graph"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(False if error_cause == "invalid_datacatalog" else True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI)._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_PAGE)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, mime_format=mime_type.to_ld_format()
        ).thenReturn(
            None if error_cause == "serialisation_failed" else DUMMY_SERIALISATION
        )
        when(
            apis.dataset.dataset_api.DataCatalogLODHandler
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        ).thenReturn()

        resp = generic_client.get(
            "offline",
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 400

        if error_cause == "invalid_datacatalog":
            assert f"The data catalog is invalid: {DUMMY_URI}." in caplog.text
        else:
            assert (
                f"Error in fetching the serialization for data catalog: {DUMMY_URI}."
                in caplog.text
            )

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        ).is_valid_data_catalog(DUMMY_URI)
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI,
            times=1
            if mime_type is MimeType.HTML and error_cause != "invalid_datacatalog"
            else 0,
        )._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler,
            times=1
            if mime_type is not MimeType.HTML and error_cause != "invalid_datacatalog"
            else 0,
        ).get_data_catalog(DUMMY_URI, mime_format=mime_type.to_ld_format())
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler,
            times=1
            if mime_type is not MimeType.HTML and error_cause != "invalid_datacatalog"
            else 0,
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        )

    finally:
        unstub()


@pytest.mark.parametrize("mime_type", [mime_type for mime_type in MimeType])
def test_get_404(
    mime_type, application_settings, generic_client, datacatalog_url, caplog
):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URI = f"http://{DUMMY_IDENTIFIER}"
    DUMMY_PAGE = "<!DOCTYPE html> <html> just something pretending to be an interesting HTML page</html>"
    DUMMY_SERIALISATION = "just something pretending to be a serialisation of a graph"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(False)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI)._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(DUMMY_PAGE)
        when(apis.dataset.dataset_api.DataCatalogLODHandler).get_data_catalog(
            DUMMY_URI, mime_format=mime_type.to_ld_format()
        ).thenReturn(DUMMY_SERIALISATION)
        when(
            apis.dataset.dataset_api.DataCatalogLODHandler
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        ).thenReturn()

        resp = generic_client.get(
            "offline",
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 404

        assert f"The data catalog doesn't exist: {DUMMY_URI}." in caplog.text

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=0
        ).is_valid_data_catalog(DUMMY_URI)
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=0
        )._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler, times=0
        ).get_data_catalog(DUMMY_URI, mime_format=mime_type.to_ld_format())
        verify(
            apis.dataset.dataset_api.DataCatalogLODHandler, times=0
        )._get_data_catalog_from_store(
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("DATA_CATALOG_GRAPH"),
        )

    finally:
        unstub()


def test_get_500(application_settings, generic_client, datacatalog_url, caplog):
    DUMMY_IDENTIFIER = 1234
    DUMMY_URI = f"http://{DUMMY_IDENTIFIER}"

    try:
        when(util.ld_util).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        ).thenReturn(DUMMY_URI)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI).is_valid_data_catalog(
            DUMMY_URI
        ).thenReturn(True)
        when(apis.dataset.dataset_api.LODDataCatalogAPI)._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        ).thenReturn(None)

        mime_type = MimeType.HTML

        resp = generic_client.get(
            "offline",
            datacatalog_url(DUMMY_IDENTIFIER),
            headers={"Accept": mime_type.value},
        )

        assert resp.status_code == 500

        assert (
            f"Could not generate proper HTML page for data catalog: {DUMMY_URI}."
            in caplog.text
        )

        verify(util.ld_util, times=1).generate_lod_resource_uri(
            DatasetApiUriLevel.DATACATALOG,
            str(DUMMY_IDENTIFIER),
            application_settings.get("BENG_DATA_DOMAIN"),
        )
        verify(apis.dataset.dataset_api.LODDataCatalogAPI, times=1).is_data_catalog(
            DUMMY_URI
        )
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        ).is_valid_data_catalog(DUMMY_URI)
        verify(
            apis.dataset.dataset_api.LODDataCatalogAPI, times=1
        )._get_lod_view_resource(
            DUMMY_URI,
            application_settings.get("SPARQL_ENDPOINT"),
            application_settings.get("URI_NISV_ORGANISATION"),
        )

    finally:
        unstub()
