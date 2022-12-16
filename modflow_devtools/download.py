import base64
import json
import os
import sys
import tarfile
import timeit
import urllib.request
from os import PathLike
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from warnings import warn

from modflow_devtools.zip import MFZipFile

_max_http_tries = 3


def get_request(url, params={}):
    """
    Get urllib.request.Request, with parameters and headers.

    This bears a GitHub API authentication token if github.com is
    in the URL and the GITHUB_TOKEN environment variable is set.

    Originally written by Mike Toews (mwtoews@gmail.com) for FloPy.
    """
    if isinstance(params, dict):
        if len(params) > 0:
            url += "?" + urllib.parse.urlencode(params)
    else:
        raise TypeError("data must be a dict")
    headers = {}

    if "github.com" in url:
        github_token = os.environ.get("GITHUB_TOKEN", None)
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

    return urllib.request.Request(url, headers=headers)


def get_releases(repo, per_page=None, quiet=False) -> List[dict]:
    """Get list of available releases."""
    req_url = f"https://api.github.com/repos/{repo}/releases"

    params = {}
    if per_page is not None:
        if per_page < 1 or per_page > 100:
            raise ValueError("per_page must be between 1 and 100")
        params["per_page"] = per_page

    request = get_request(req_url, params=params)
    num_tries = 0
    while True:
        num_tries += 1
        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                result = resp.read()
                break
        except urllib.error.HTTPError as err:
            if err.code == 401 and os.environ.get("GITHUB_TOKEN"):
                raise ValueError("GITHUB_TOKEN env is invalid") from err
            elif err.code == 403 and "rate limit exceeded" in err.reason:
                raise ValueError(
                    f"use GITHUB_TOKEN env to bypass rate limit ({err})"
                ) from err
            elif err.code in (404, 503) and num_tries < _max_http_tries:
                # GitHub sometimes returns this error for valid URLs, so retry
                print(f"URL request {num_tries} did not work ({err})")
                continue
            raise RuntimeError(f"cannot retrieve data from {req_url}") from err

    releases = json.loads(result.decode())
    if not quiet:
        print(f"Found {len(releases)} releases for {repo}")

    return releases


def get_release(repo, tag="latest", quiet=False) -> dict:
    """Get info about a particular release."""
    api_url = f"https://api.github.com/repos/{repo}"
    req_url = (
        f"{api_url}/releases/latest"
        if tag == "latest"
        else f"{api_url}/releases/tags/{tag}"
    )
    request = get_request(req_url)
    releases = None
    num_tries = 0

    while True:
        num_tries += 1
        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                result = resp.read()
                remaining = int(resp.headers["x-ratelimit-remaining"])
                if remaining <= 10:
                    warn(
                        f"Only {remaining} GitHub API requests remaining "
                        "before rate-limiting"
                    )
                break
        except urllib.error.HTTPError as err:
            if err.code == 401 and os.environ.get("GITHUB_TOKEN"):
                raise ValueError("GITHUB_TOKEN env is invalid") from err
            elif err.code == 403 and "rate limit exceeded" in err.reason:
                raise ValueError(
                    f"use GITHUB_TOKEN env to bypass rate limit ({err})"
                ) from err
            elif err.code == 404:
                if releases is None:
                    releases = get_releases(repo, quiet)
                if tag not in releases:
                    raise ValueError(
                        f"Release {tag} not found (choose from {', '.join(releases)})"
                    )
            elif err.code == 503 and num_tries < _max_http_tries:
                # GitHub sometimes returns this error for valid URLs, so retry
                warn(f"URL request {num_tries} did not work ({err})")
                continue
            raise RuntimeError(f"cannot retrieve data from {req_url}") from err

    release = json.loads(result.decode())
    tag_name = release["tag_name"]
    if not quiet:
        print(f"fetched release {tag_name!r} from {repo}")

    return release


def list_release_assets(repo, tag="latest", quiet=False) -> List[dict]:
    pass


def list_artifacts(
    repo, name=None, per_page=None, max_pages=None, quiet=False
) -> List[dict]:
    """
    List repository artifacts via the GitHub API, optionally filtering by name pattern.
    """

    msg = f"artifact(s) for {repo}" + (
        f" matching name {name}" if name else ""
    )
    url = f"https://api.github.com/repos/{repo}/actions/artifacts"
    page = 0
    params = {}

    if name is not None:
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError(f"name must be a non-empty string")
        params["name"] = name

    if per_page is not None:
        if per_page < 1 or per_page > 100:
            raise ValueError("per_page must be between 1 and 100")
        params["per_page"] = int(per_page)

    def get_result():
        tries = 0
        params["page"] = page
        request = get_request(url, params=params)
        while True:
            tries += 1
            try:
                print(f"Fetching {msg} (page {page}, size {per_page})")
                with urllib.request.urlopen(request, timeout=10) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as err:
                if err.code == 401 and os.environ.get("GITHUB_TOKEN"):
                    raise ValueError("GITHUB_TOKEN env is invalid") from err
                elif err.code == 403 and "rate limit exceeded" in err.reason:
                    raise ValueError(
                        f"use GITHUB_TOKEN env to bypass rate limit ({err})"
                    ) from err
                elif err.code in (404, 503) and tries < _max_http_tries:
                    # GitHub sometimes returns this error for valid URLs, so retry
                    print(f"URL request try {tries} did not work ({err})")
                    continue
                raise RuntimeError(f"cannot retrieve data from {url}") from err

    artifacts = []
    diff = 1
    max_pages = max_pages if max_pages else sys.maxsize
    while diff > 0 and page < max_pages:
        page += 1
        result = get_result()
        total = result["total_count"]
        if page == 1:
            print(f"Repo {repo} has {total} {msg}")

        artifacts.extend(result["artifacts"])
        diff = total - len(artifacts)

    if not quiet:
        print(f"Found {len(artifacts)} {msg}")

    return artifacts


def download_artifact(
    repo, id, path: Optional[PathLike] = None, delete_zip=True, quiet=False
):
    url = f"https://api.github.com/repos/{repo}/actions/artifacts/{id}/zip"
    request = urllib.request.Request(url)
    if "github.com" in url:
        github_token = os.environ.get("GITHUB_TOKEN", None)
        if github_token:
            request.add_header("Authorization", f"Bearer {github_token}")

    zip_path = Path(path).expanduser().absolute() / f"{str(uuid4())}.zip"

    tries = 0
    while True:
        tries += 1
        try:
            with urllib.request.urlopen(request) as url_file, open(
                zip_path, "wb"
            ) as out_file:
                content = url_file.read()
                out_file.write(content)
                break
        except urllib.error.HTTPError as err:
            if tries < _max_http_tries:
                print(f"URL request try {tries} did not work ({err})")
                continue
            else:
                raise RuntimeError(f"cannot retrieve data from {url}") from err

    if not quiet:
        print(f"Uncompressing: {zip_path}")

    z = MFZipFile(zip_path)
    z.extractall(str(path))
    z.close()

    # delete the zipfile
    if delete_zip:
        if not quiet:
            print(f"Deleting zipfile {zip_path}")
        zip_path.unlink()


def download_and_unzip(
    url: str,
    path: Optional[PathLike] = None,
    delete_zip=True,
    verbose=False,
):
    """
    Download and unzip a zip file from a URL.
    The filename must be the last element in the URL.

    Parameters
    ----------
    url : str
        url address for the zip file
    path : PathLike
        path where the zip file will be saved (default is current path)
    delete_zip : bool
        boolean indicating if the zip file should be deleted after it is
        unzipped (default is True)
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------

    """

    path = Path(path if path else os.getcwd())
    path.mkdir(exist_ok=True)

    if verbose:
        print(f"Downloading {url}")

    tic = timeit.default_timer()

    # download zip file
    file_path = path / url.split("/")[-1]
    request = urllib.request.Request(url)
    if "github.com" in url:
        github_token = os.environ.get("GITHUB_TOKEN", None)
        if github_token:
            request.add_header("Authorization", f"Bearer {github_token}")

    tries = 0
    while True:
        tries += 1
        try:
            with urllib.request.urlopen(request) as url_file, open(
                file_path, "wb"
            ) as out_file:
                content = url_file.read()
                out_file.write(content)

                # if verbose, print content length (if available)
                tag = "Content-length"
                if verbose and tag in url_file.headers:
                    file_size = url_file.headers[tag]
                    len_file_size = len(file_size)
                    file_size = int(file_size)

                    bfmt = "{:" + f"{len_file_size}" + ",d}"
                    sbfmt = (
                        "{:>"
                        + f"{len(bfmt.format(int(file_size)))}"
                        + "s} bytes"
                    )
                    print(
                        f"   file size: {sbfmt.format(bfmt.format(int(file_size)))}"
                    )

                break
        except urllib.error.HTTPError as err:
            if tries < _max_http_tries:
                print(f"URL request try {tries} did not work ({err})")
                continue

    # write the total download time
    toc = timeit.default_timer()
    tsec = round(toc - tic, 2)
    if verbose:
        print(f"\ntotal download time: {tsec} seconds")

    # Unzip the file, and delete zip file if successful.
    if "zip" in file_path.suffix or "exe" in file_path.suffix:
        z = MFZipFile(file_path)
        try:
            if verbose:
                print(f"Uncompressing: {file_path}")

            # extract the files
            z.extractall(str(path))
        except:
            p = "Could not unzip the file. Stopping."
            raise Exception(p)
        z.close()

        # delete the zipfile
        if delete_zip:
            if verbose:
                print(f"Deleting zipfile {file_path}")
            file_path.unlink()
    elif "tar" in file_path.suffix:
        ar = tarfile.open(file_path)
        ar.extractall(path=str(path))
        ar.close()

        # delete the zipfile
        if delete_zip:
            if verbose:
                print(f"Deleting zipfile {file_path}")
            file_path.unlink()

    if verbose:
        print(f"Done downloading and extracting {file_path.name} to {path}")
