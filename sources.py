"""One allowlist for where media may come from and what it may be called.

Official US science agencies (USGS, NOAA, NASA) are accepted for every media type.
Wikimedia Commons is accepted ONLY for public-domain historical illustrations
(e.g. the 1888 Royal Society Krakatoa report), whose original publication must be
cited in the asset description. Rights are still verified per file by a human.
"""
from pathlib import Path
from urllib.parse import urlparse

USGS_S3 = "usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com"
OFFICIAL_SUFFIXES = ("usgs.gov", "noaa.gov", "nasa.gov")
MEDIA_TYPES = ("real_video", "photo", "satellite_observation", "historical_illustration",
               "model_animation", "diagram")
MOTION_SUFFIXES = (".mp4", ".mov", ".m4v")
STILL_SUFFIXES = (".png", ".jpg", ".jpeg")


def _official(host):
    return bool(host) and any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES)


def media_host_ok(url, media_type):
    parsed = urlparse(url or "")
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        return False
    return (_official(host) or host == USGS_S3
            or (host == "upload.wikimedia.org" and media_type == "historical_illustration"))


def source_host_ok(url, media_type):
    parsed = urlparse(url or "")
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        return False
    return _official(host) or (host == "commons.wikimedia.org" and media_type == "historical_illustration")


def filename_ok(filename):
    return (isinstance(filename, str) and Path(filename).name == filename
            and Path(filename).suffix.lower() in MOTION_SUFFIXES + STILL_SUFFIXES)


def is_still(filename):
    return Path(filename).suffix.lower() in STILL_SUFFIXES
