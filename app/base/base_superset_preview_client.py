# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc

from flask import Response as FlaskResponse, make_response, jsonify
from http import HTTPStatus
from requests import Response
from typing import Dict

from app.base.base_preview_client import BasePreviewClient
from app.models.preview_data import ColumnItem, PreviewData, PreviewDataSchema


class BaseSupersetPreviewClient(BasePreviewClient):
    @abc.abstractmethod
    def __init__(self) -> None:
        self.headers = {}  # type: Dict

    @abc.abstractmethod
    def post_to_sql_json(self, *, params: Dict, headers: Dict) -> Response:
        """
        Returns the post response from Superset's `sql_json` endpoint
        """
        pass  # pragma: no cover

    def get_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> FlaskResponse:
        """
        Returns a FlaskResponse object, where the response data represents a json object
        with the preview data accessible on 'preview_data' key. The preview data should
        match app.models.preview_data.PreviewDataSchema
        """
        try:
            # Clone headers so that it does not mutate instance's state
            headers = dict(self.headers)

            # Merge optionalHeaders into headers
            if optionalHeaders is not None:
                headers.update(optionalHeaders)

            # Request preview data
            response = self.post_to_sql_json(params=params, headers=headers)

            # Verify and return the results
            response_dict = response.json()
            columns = [ColumnItem(c['name'], c['type']) for c in response_dict['columns']]
            preview_data = PreviewData(columns, response_dict['data'])
            data = PreviewDataSchema().dump(preview_data)[0]
            errors = PreviewDataSchema().load(data)[1]
            if not errors:
                payload = jsonify({'preview_data': data})
                return make_response(payload, response.status_code)
            else:
                return make_response(jsonify({'preview_data': {}}), HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception:
            return make_response(jsonify({'preview_data': {}}), HTTPStatus.INTERNAL_SERVER_ERROR)
