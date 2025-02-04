import configparser
import hashlib
import os
import re
import requests
from datetime import datetime
from typing import Optional, Tuple
import pygit2  # type: ignore
import urllib3.util
import version_diff_analyse


GH_REPO_REGEX = r'(?:https?://)?(?:www\.)?github\.com/(?:[\w-]+/)(?:[\w-]+)'
GH_REPO_OWNER_REGEX = r'(?:https?://)?(?:www\.)?github\.com/([\w-]+)/([\w-]+)'


def extract_owner_and_repo(url) -> Tuple[Optional[str], Optional[str]]:
    match = re.search(GH_REPO_OWNER_REGEX, url)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        #print(match.group(0))
        return owner, repo
    return None, None


def find_best_github_candidate(all_candidates_and_highlighted_link, name):
    """
    This method goes through multiple URLs and checks which one is the most suitable to be used as GitHub URL for
    the project repository.
    If the repository homepage is a GitHub URL, it is used in priority
    """
    candidates, best_github_candidate = all_candidates_and_highlighted_link

    # if the project url is a GitHub repository, we should follow this as an instruction. Users will click on it
    if best_github_candidate is not None:
        best_github_candidate = best_github_candidate.replace("http://", "https://")
        url = urllib3.util.parse_url(best_github_candidate)
        if url.host == "github.com":
            return best_github_candidate
    clean_candidates = []
    for entry in candidates:
        # let's do some cleanup
        url = urllib3.util.parse_url(entry)
        if url.host != "github.com":
            continue
        if url.scheme == "http":
            entry = entry.replace("http://", "https://")
        clean_candidates.append(entry)
    for entry in clean_candidates:
        if f"/{name.lower()}" in entry.lower():
            return entry
    # solution 1 did not work, let's be a bit more aggressive
    for entry in clean_candidates:
        owner, repo = extract_owner_and_repo(entry)
        if repo is not None and (
                # Idea: replace by if two strings have a Levenshtein distance < X% of string length
                repo.lower() in name.lower() or name.lower() in repo.lower()):
            return entry
    return None


def dict_generator(indict, pre=None):
    """
    This generator recursively go through an arbitrary dict
    Each iteration will be an array containing the path of all leaves of the dict
    """
    pre = pre[:] if pre else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in dict_generator(value, pre + [key]):
                    yield d
            elif isinstance(value, list) or isinstance(value, tuple):
                for v in value:
                    for d in dict_generator(v, pre + [key]):
                        yield d
            else:
                yield pre + [key, value]
    else:
        yield pre + [indict]


def get_file_hash(path):
    with open(path, 'rb') as f:
        # Read the contents of the file
        file_contents = f.read()
        # Create a hash object
        hash_object = hashlib.sha256()
        # Feed the file contents to the hash object
        hash_object.update(file_contents)
        # Get the hexadecimal hash value
        return hash_object.hexdigest(), str(file_contents).strip().splitlines()


def _ensure_proper_url(url):
    parsed = urllib3.util.parse_url(url)
    if parsed.scheme is None:
        url = f"https://{url}"
    return url


def find_github_candidates(package_info) -> Tuple[set[str], Optional[str]]:
    infos = package_info["info"]
    homepage = None
    project_urls = infos.get("project_urls", {})
    # In some cases, the "project_urls" key is set, but is set to None
    if project_urls is None:
        return set(), None
    if "Homepage" in project_urls:
        homepage = package_info["info"]["project_urls"]["Homepage"]
    github_urls = set()
    for dict_path in dict_generator(infos):
        leaf = dict_path[-1]
        if type(leaf) is not str:
            continue
        res = re.findall(GH_REPO_REGEX, leaf)
        if len(res) > 0:
            for cd in res:
                github_urls.add(_ensure_proper_url(cd.strip()))
    best = None
    if homepage in github_urls:
        if homepage is not None and isinstance(homepage, str):
            response = requests.get(homepage)
            if response.status_code == 200:
                best = _ensure_proper_url(homepage)
    return github_urls, best


EXCLUDED_EXTENSIONS = [".rst", ".md", ".txt"]


def exclude_result(file_name, repo_root, pkg_root):
    """
    This method filters out some results that are known false positives:
    * if the file is a documentation file (based on its extension)
    * if the fil is an setup.cfg file with the egg_info claim present on Pypi and not on GitHub
    """
    for extension in EXCLUDED_EXTENSIONS:
        if file_name.endswith(extension):
            return True
    if file_name.endswith("setup.cfg"):
        repo_cfg = configparser.ConfigParser()
        repo_cfg.read(os.path.join(repo_root, file_name))
        pkg_cfg = configparser.ConfigParser()
        pkg_cfg.read(os.path.join(pkg_root, file_name))
        repo_sections = list(repo_cfg.keys())
        pkg_sections = list(pkg_cfg.keys())
        if "egg_info" in pkg_sections and "egg_info" not in repo_sections:
            return True
    return False


def find_mismatch_for_tag(repo, tag, base_path, repo_path):
    repo.checkout(tag)
    mismatch = []
    for root, dirs, files in os.walk(base_path):
        relative_path = os.path.relpath(root, base_path)
        repo_root = os.path.join(repo_path, relative_path)
        if not os.path.exists(repo_root):
            continue
        repo_files = list(filter(
            lambda x: os.path.isfile(os.path.join(repo_root, x)),
            os.listdir(repo_root)
        ))
        for file_name in repo_files:
            if not file_name.endwith('.py'):  # ignore files we don't have in the distribution
                continue
            if file_name not in files:  # ignore files we don't have in the distribution
                continue
            repo_hash, repo_content = get_file_hash(os.path.join(repo_root, file_name))
            pkg_hash, pkg_content = get_file_hash(os.path.join(root, file_name))
            if repo_hash != pkg_hash:
                if exclude_result(file_name, repo_root, root):
                    continue
                res = {
                    "file": os.path.join(relative_path, file_name),
                    "repo_sha256": repo_hash,
                    "pkg_sha256": pkg_hash
                }
                mismatch.append(res)
    return mismatch


def find_suitable_tags_in_list(tags, version):
    tag_candidates = []
    for tag_name in tags:
        if tag_name.endswith(version):
            tag_candidates.append(tag_name)
    return tag_candidates


def find_suitable_tags(repo, version):
    tags_regex = re.compile('^refs/tags/(.*)')
    tags = []
    for ref in repo.references:
        match = tags_regex.match(ref)
        if match is not None:
            tags.append(match.group(0))
    return find_suitable_tags_in_list(tags, version)

    
RULE_NAME = "repository_integrity_mismatch"
def detect(package_info, path: Optional[str] = None, name: Optional[str] = None,
            version: Optional[str] = None) -> tuple[bool, str]:
    if name is None:
        raise Exception("Detector needs the name of the package")
    if path is None:
        raise Exception("Detector needs the path of the package")

    # let's extract a source repository (GitHub only for now) if we can
    github_urls, best_github_candidate = find_github_candidates(package_info)
    if len(github_urls) == 0:
        return False, "Could not find any GitHub url in the project's description"
    # now, let's find the right url

    github_url = find_best_github_candidate((github_urls, best_github_candidate), name)

    print(github_url)
    
    if github_url is None:
        return False, "Could not find a good GitHub url in the project's description"

    # ok, now let's try to find the version! (I need to know which version we are scanning)
    if version is None:
        version = package_info["info"]["version"]
    if version is None:
        raise Exception("Could not find suitable version to scan")
    tmp_dir = os.path.dirname(path)
    if tmp_dir is None:
        raise Exception("no current scanning directory")
    
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    repo_path = os.path.join(tmp_dir,time_str, name)
    
    try:
        #os.system('cd path;'+'git clone '+github_url)
        repo = pygit2.clone_repository(url=github_url, path=repo_path) 
    except pygit2.GitError as git_error:
        # Handle generic Git-related errors
        raise Exception(f"Error while cloning repository {str(git_error)} with github url {github_url}")
    except Exception as e:
        # Catch any other unexpected exceptions
        raise Exception(f"An unexpected error occured: {str(e)}.  github url {github_url}")

    tag_candidates = find_suitable_tags(repo, version)
    #print(tag_candidates)
    if len(tag_candidates) == 0:
        return False, "Could not find any suitable tag in repository"
    target_tag = None
    # TODO: this one is a bit weak. let's find something stronger - maybe use the closest string?
    for tag in tag_candidates:
        target_tag = tag
    tmp_file = version_diff_analyse.github_diff(path,repo_path)
    if tmp_file == '':
        return 1,'Integrity check is ok!'
    else:
        return tmp_file,'May be malicious,integrity compromise!!'
    
    #return len(mismatch) > 0, f"Some files present in the package are different from the ones on GitHub for " \
    #                            f"the same version of the package: \n{message}"
 