import requests
from typing import Dict, Optional
import os
from urllib.parse import urlparse


class BooruAPIError(Exception):
    pass

class NetworkConnectionError(Exception):
    pass

class RateLimitError(Exception):
    pass

class BooruNotFoundError(Exception):
    pass


class Booru():
    gb = "gelbooru"
    r34 = "rule34"
    safe = "safebooru"
    e621net = "e621"
    
    selection = gb

    gelbooru_like = [gb, safe, r34]
    e621_like = [e621net]

    def gelbooru(self):
        """
        Set the booru to gelbooru.

        """
        self.selection = self.gb

    def safebooru(self):
        """
        Set the booru to safebooru.

        """
        self.selection = self.safe

    
    def rule34(self):
        """
        Set the booru to rule34.

        """
        self.selection = self.r34

    
    def e621(self, username: str, project: str="boorureq", version: str="1.0"):
        """
        Set the booru to e621.

        Args:
            username (str): The e621 username to use in the useragent string.
            project (str, optional): The project name to use in the useragent string. Defaults to "boorureq".
            version (str, optional): The version to use in the useragent string. Defaults to "1.0".

        """
        self.selection = self.e621net

        self.useragent = f"{project}/{version} (by {username} on e621.net)"


    def __init__(self):
        """
        Initialize a Booru instance with default settings.

        The default booru selection is set to "gelbooru". This can be changed using the desired booru method if it exists on class.
        """
        pass


 # Replace with the actual base URL

def _make_request(request: str, useragent: str = None) -> Dict:
    """Make a request to the API with authentication."""
    headers = {}    
    if useragent:
        headers = {"User-Agent": useragent}
    else:
        headers = None
    
    response = requests.get(request, headers=headers)
    
    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded. Please wait and try again.")
    
    if response.status_code == 404:
        raise BooruNotFoundError("Booru not found.")
    
    if response.status_code != 200:
        print(response.status_code)
        raise NetworkConnectionError("Network connection error. Please check your internet connection.")
    
    response.raise_for_status()
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise BooruAPIError(f"Error decoding JSON: {response.text}")

def get_posts_gelbooru(base: str, limit: int = 100, pid: int = 0, tags: Optional[list] = None, 
              exclude_tags: Optional[list] = None, cid: Optional[int] = None, post_id: Optional[int] = None) -> Dict:
    """
    Get posts from a Gelbooru-style booru.

    Args:
        base: The domain name of the booru. Should be one of "gelbooru", "safebooru", or "rule34".
        limit: The maximum number of posts to retrieve.
        pid: The page number to retrieve.
        tags: The tags to search for.
        exclude_tags: The tags to exclude from the search.
        cid: The collection ID to retrieve.
        post_id: The ID of the post to retrieve.

    Returns:
        A dictionary containing the requested posts.
    """
    endpoint = "/index.php?"

    if base == "gelbooru":
        base_url = "https://gelbooru.com"
    elif base == "safebooru":
        base_url = "https://safebooru.org"
    elif base == "rule34":
        base_url = "https://api.rule34.xxx"
    else:
        raise ValueError(f"Invalid booru for this function.")
    
    
    params = {
        "json": "1",
        "page": "dapi",
        "s": "post",
        "q": "index",
        "limit": str(limit),
        "pid": str(pid)
    }
    tag_query = ""

    if tags:
        for tag in tags:
            tag_query += f"+{tag}"

    if exclude_tags:
        for tag in exclude_tags:
            tag_query += f"+-{tag}"

    if tag_query != "":
        tag_query = tag_query[1:]
        params["tags"] = tag_query

    if tag_query:
        params["tags"] = tag_query

    if cid:
        params["cid"] = str(cid)
    if post_id:
        params["id"] = str(post_id)
        
    request = f"{base_url}{endpoint}"
    
    for key, value in params.items():
        request += f"&{key}={value}"
    
    return _make_request(request)


def get_posts_e621net(useragent: str, page: int = 0, tags: list = [], exclude_tags: list = [], limit: int = 100):
    """
    Get posts from e621.net.

    Args:
        page: The page of posts to retrieve.
        tags: A list of tags to search for.
        exclude_tags: A list of tags to exclude from the search.
        limit: The maximum number of posts to retrieve.

    Returns:
        A list of posts.
    """
    params = {
        "limit": str(limit),
        "page": str(page),
    }

    full_tag = ""
    if tags:
        for tag in tags:
            full_tag += f"+{tag}"

    if exclude_tags:
        for tag in exclude_tags:
            full_tag += f"+-{tag}"

    if full_tag != "":
        full_tag = full_tag[1:]
        params["tags"] = full_tag

    request = f"https://e621.net/posts.json?"
    
    for key, value in params.items():
        request += f"&{key}={value}"
    
    return _make_request(request, useragent=useragent)
    

# Get posts from a booru
def get_posts(booru: Booru, page: int, tags: list, exclude_tags: list = [], limit: int = 100, cid: Optional[int] = None, post_id: Optional[int] = None):
    """
    Get posts from a booru in a single function.

    Args:
        booru: The name of the booru to query.
        page: The page of posts to retrieve.
        tags: The tags to search for.
        exclude_tags: The tags to exclude from the search.
        limit: The maximum number of posts to retrieve.
        pid: The pid of the tag to search for.
        cid: The cid of the tag to search for. Defaults to None.
        post_id: The id of the post to search for. Defaults to None.

    Returns:
        A dict with a dict of posts.
    """


    posts = {}
    selection = booru.selection

    if selection in Booru.gelbooru_like:
        posts = get_posts_gelbooru(base=selection, pid=page, tags=tags, exclude_tags=exclude_tags, limit=limit, cid=cid, post_id=post_id)

        if isinstance(posts, dict) and "post" in posts:
            posts = posts["post"]
        
    if selection in Booru.e621_like:
        posts = get_posts_e621net(useragent=booru.useragent, tags=tags, exclude_tags=exclude_tags, limit=limit, page=page)

        posts = posts["posts"]
        index = 0

        # Fix dict to download_posts function
        for post in posts:
            # Image url
            posts[index]["file_url"] = post["file"]["url"]
            
            tags_string = ""
            # Tags
            for value in post["tags"].values():
                for tag in value:
                    tags_string += f"{tag} "
            
            posts[index]["tags"] = tags_string

            index += 1


    return posts
    

def download_posts(posts, output_dir="downloads", verbose=False):
    """
    Download files from posts and save them locally.

    Args:
        posts: The list or dictionary of posts returned from a booru API.
        output_dir: Directory to save downloaded files.

    Returns:
        A list with a dict of file paths of downloaded files and its tags, the number of files downloaded and total expected files
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    downloaded_files = {}

    downloaded = 0
    expected = len(posts)
    index = 0
    for post in posts:
        downloaded += 1
        index += 1

        try:
            percent = ((index-1)/expected)*100
        except ZeroDivisionError:
            percent = 0.00

        if verbose:
            print(f"Downloading... {percent:.2f}% (Downloaded {downloaded-1} of {expected} files)")

        file_url = post.get("file_url") or post.get("large_file_url") or post.get("preview_url")
        if not file_url:

            downloaded -= 1
            continue

        # Extract file name and download
        file_name = os.path.basename(urlparse(file_url).path)
        file_path = os.path.join(output_dir, file_name)
        

        
        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            downloaded -= 1
            
            continue
        
        
        downloaded_files[file_path] = post.get("tags").split(" ")
    
    if verbose:
        print(f"Downloaded {downloaded} of {expected} files")
    return [downloaded_files, downloaded, expected]


if __name__ == "__main__":
    booru = Booru()

    booru.e621(username="piddemont")
    
    posts = get_posts(booru=booru, page=1, tags=["yaoi"], exclude_tags=["solo"], limit=1)
    print(download_posts(posts, verbose=True))
