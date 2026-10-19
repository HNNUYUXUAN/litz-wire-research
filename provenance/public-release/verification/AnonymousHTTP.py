"""Credential-free urllib transport shared by public acceptance helpers."""
import urllib.request
from urllib.parse import urlsplit, urlunsplit

FORBIDDEN = {"authorization", "proxy-authorization", "cookie", "cookie2"}


def safe_url(url):
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def trusted_url(url):
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    return (parsed.scheme == "https" and not parsed.username and not parsed.password
            and parsed.port in (None, 443)
            and (host in {"github.com", "api.github.com", "codeload.github.com"}
                 or host.endswith(".githubusercontent.com")
                 or host == "github-production-release-asset-2e65be.s3.amazonaws.com"))


class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted_url(newurl):
            raise ValueError("untrusted_public_download_redirect")
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            for key in [*new.headers, *new.unredirected_hdrs]:
                if key.casefold() in FORBIDDEN:
                    new.remove_header(key)
        return new


class RequestAudit(urllib.request.BaseHandler):
    handler_order = 999

    def __init__(self, records):
        self.records = records

    def http_request(self, request):
        names = sorted(key.casefold() for key, _ in request.header_items())
        forbidden = sorted(set(names) & FORBIDDEN)
        record = {"method": request.get_method(), "url": safe_url(request.full_url),
                  "header_names": names, "credential_headers": forbidden}
        self.records.append(record)
        if forbidden or not trusted_url(request.full_url):
            raise ValueError("credential_header_or_untrusted_download_blocked")
        return request

    https_request = http_request


def opener(records, build=urllib.request.build_opener):
    return build(urllib.request.ProxyHandler({}), Redirect(), RequestAudit(records))
