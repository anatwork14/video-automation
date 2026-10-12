"""One allowlist for where media may come from and what it may be called.

Official US science agencies (USGS, NOAA, NASA) are accepted for every media type.
Wikimedia Commons and the Internet Archive are accepted ONLY for public-domain
historical illustrations (e.g. the 1888 Royal Society Krakatoa report scans), whose
original publication must be cited in the asset description. Rights are still verified per file by a human.
"""
from pathlib import Path
from urllib.parse import urlparse

USGS_S3 = "usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com"
USGS_IMAGE_S3 = "d9-wret.s3.us-west-2.amazonaws.com"  # USGS website image bucket (www.usgs.gov/media/images)
NOAA_NESDIS_S3 = "nesdis-prod.s3.amazonaws.com"         # target of www.nesdis.noaa.gov/s3dl download links
AGENCY_BUCKETS = (USGS_S3, USGS_IMAGE_S3, NOAA_NESDIS_S3)
HISTORICAL_HOSTS = ("upload.wikimedia.org", "commons.wikimedia.org", "archive.org")  # PD-by-age scans only
OFFICIAL_SUFFIXES = ("usgs.gov", "noaa.gov", "nasa.gov", "tsunami.gov", "weather.gov")  # tsunami.gov, weather.gov: NOAA/NWS
MEDIA_TYPES = ("real_video", "photo", "satellite_observation", "historical_illustration",
               "model_animation", "diagram")
MOTION_SUFFIXES = (".mp4", ".mov", ".m4v")
STILL_SUFFIXES = (".png", ".jpg", ".jpeg")


def _official(host):
    return bool(host) and any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES)


def _historical(host):
    return any(host == h or host.endswith("." + h) for h in HISTORICAL_HOSTS)


def media_host_ok(url, media_type):
    parsed = urlparse(url or "")
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        return False
    return (_official(host) or host in AGENCY_BUCKETS
            or (_historical(host) and media_type == "historical_illustration"))


def source_host_ok(url, media_type):
    parsed = urlparse(url or "")
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        return False
    return _official(host) or (_historical(host) and media_type == "historical_illustration")


def filename_ok(filename):
    return (isinstance(filename, str) and Path(filename).name == filename
            and Path(filename).suffix.lower() in MOTION_SUFFIXES + STILL_SUFFIXES)


def is_still(filename):
    return Path(filename).suffix.lower() in STILL_SUFFIXES


def evidence_host_ok(host):
    """Science evidence: official US science agencies, or a peer-reviewed paper via doi.org."""
    return _official(host or "") or host == "doi.org"
