import json
from uuid import UUID

from qgis.core import QgsBlockingNetworkRequest, QgsFeedback
from qgis.PyQt.QtCore import QUrl, QUrlQuery, QUuid
from qgis.PyQt.QtNetwork import QNetworkRequest


def coerce_uuid_to_str(uuid: str | UUID | QUuid) -> str:
    if isinstance(uuid, UUID):
        return str(uuid)
    elif isinstance(uuid, QUuid):
        return uuid.toString(QUuid.StringFormat.WithoutBraces)
    elif isinstance(uuid, str):
        return uuid
    else:
        raise TypeError(f"Expected UUID or str, got {type(uuid)}")


class Canceled(Exception):
    pass


class BaseClient:
    base_path: str

    def __init__(
        self, base_url: str, authcfg: str, feedback: QgsFeedback | None = None
    ):
        self._base_url = base_url
        self._feedback = feedback
        self._request = QgsBlockingNetworkRequest()
        self._request.setAuthCfg(authcfg)

    def _get(self, path: str, query: QUrlQuery) -> dict | list:
        return self._get_with_headers(path, query)[0]

    def _get_with_headers(
        self, path: str, query: QUrlQuery
    ) -> tuple[dict | list, dict] | Canceled:
        url = QUrl(f"{self._base_url.rstrip('/')}{self.base_path.rstrip('/')}{path}")
        url.setQuery(query)

        req = QNetworkRequest(url)
        req.setRawHeader(b"Accept", b"application/json, application/geo+json")

        if self._request.get(
            req, feedback=self._feedback
        ) != QgsBlockingNetworkRequest.ErrorCode.NoError or (
            self._feedback is not None and self._feedback.isCanceled()
        ):
            if self._feedback is not None and self._feedback.isCanceled():
                raise Canceled()
            else:
                reply = self._request.reply().content().data().decode()
                raise Exception(
                    "Network error: " + self._request.errorMessage() + "\n" + reply
                )

        response = self._request.reply().content().data().decode()
        return json.loads(response), {
            str(header, encoding="utf-8").lower(): str(
                self._request.reply().rawHeader(header), encoding="utf-8"
            )
            for header in self._request.reply().rawHeaderList()
        }

    def _post(
        self, path: str, query: QUrlQuery, data: bytes | dict | list
    ) -> dict | list | Canceled:
        url = QUrl(f"{self._base_url.rstrip('/')}{self.base_path.rstrip('/')}{path}")
        url.setQuery(query)

        req = QNetworkRequest(url)
        req.setRawHeader(b"Accept", b"application/json")

        if not isinstance(data, bytes):
            data = json.dumps(data).encode("utf-8")
            req.setRawHeader(b"Content-Type", b"application/json")

        if self._request.post(
            req, data, feedback=self._feedback
        ) != QgsBlockingNetworkRequest.ErrorCode.NoError or (
            self._feedback is not None and self._feedback.isCanceled()
        ):
            if self._feedback is not None and self._feedback.isCanceled():
                raise Canceled()
            else:
                reply = self._request.reply().content().data().decode()
                raise Exception(
                    "Network error: " + self._request.errorMessage() + "\n" + reply
                )

        response = self._request.reply().content().data().decode()
        return json.loads(response)
