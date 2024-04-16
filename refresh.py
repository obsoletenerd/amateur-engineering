# from github import Github
# from github import Auth
from dotenv import load_dotenv
import requests
import yaml
import urllib.parse

load_dotenv()  # take environment variables from .env.

# auth = Auth.Token(os.getenv("GITHUB_KEY"))
# g = Github(auth=auth)

repo_url = "https://raw.githubusercontent.com/senwerks/AmateurEngineering/main/contributors.yaml"


def get_github(username, posts_url):
    print(f"Grabbing {username}'s markdown files from GitHub...")
    # Convert the GitHub web URL to the API URL
    # Correctly handle the conversion from:
    # https://github.com/user/repo/tree/branch/path/to/folder
    # to:
    # https://api.github.com/repos/user/repo/contents/path/to/folder?ref=branch
    if "github.com" in posts_url and "/tree/" in posts_url:
        base_url = "https://api.github.com/repos"
        parts = posts_url.split("/")
        user = parts[3]
        repo = parts[4]
        branch = parts[6]
        path = "/".join(parts[7:])  # This is the path within the repository
        api_url = f"{base_url}/{user}/{repo}/contents/{path}?ref={branch}"
        print(f"Converted WWW URL to API URL: {api_url}")
    else:
        return "Invalid GitHub URL"

    # Make a request to the GitHub API
    response = requests.get(api_url)
    if response.status_code == 200:
        files = response.json()
        md_files = []
        for file in files:
            if file["type"] == "file" and file["name"].endswith(".md"):
                # Convert the API file URL to the web view URL
                web_url = file["html_url"]
                md_files.append(web_url)
        return md_files
    else:
        return "Failed to retrieve data from GitHub API"


def parse_gitlab_url(posts_url):
    """Parse a GitLab URL to extract the API endpoint components."""
    print(f"Parsing URL: {posts_url}")
    if "gitlab.com" not in posts_url:
        return None, None, None

    # Normalize and split the URL to parts
    parts = posts_url.replace("-/tree/", "/tree/").split("/")
    try:
        # Extract base parts
        base_index = parts.index("gitlab.com") + 1
        namespace = "/".join(parts[base_index : base_index + 2])
        # URL encode the namespace for API usage
        encoded_namespace = urllib.parse.quote_plus(namespace)
        project_api_base = (
            f"https://gitlab.com/api/v4/projects/{encoded_namespace}/repository/tree"
        )

        # Find the tree index and extract branch and path
        if "tree" in parts:
            tree_index = parts.index("tree") + 1
            branch = parts[tree_index]
            path = "/".join(parts[tree_index + 1 :])
        else:
            branch = "main"
            path = ""

        print(
            f"Namespace: {namespace}, Encoded Namespace: {encoded_namespace}, Branch: {branch}, Path: {path}"
        )
        print(f"API URL: {project_api_base}, Branch: {branch}, Path: {path}")
        return project_api_base, branch, path
    except (ValueError, IndexError):
        return None, None, None


def get_gitlab(username, posts_url):
    print(f"Grabbing {username}'s markdown files from GitLab URL: {posts_url}")
    api_base, branch, path = parse_gitlab_url(posts_url)

    if not api_base:
        return "Invalid GitLab URL or unable to parse necessary details"

    params = {"ref": branch, "path": path}
    print(f"GitLab API URL: {api_base} with parameters {params}")

    # Make the API request
    response = requests.get(api_base, params=params)
    if response.status_code == 200:
        items = response.json()
        md_files = []
        for item in items:
            if item["type"] == "blob" and item["name"].endswith(".md"):
                file_namespace = urllib.parse.quote_plus(
                    "/".join(api_base.split("/")[4:6])
                )
                md_url = f"https://gitlab.com/{file_namespace}/-/blob/{branch}/{item['path']}"
                md_files.append(md_url)
        return md_files
    else:
        return f"Failed to retrieve data from GitLab API with status {response.status_code}"


def get_other(username, posts_url):
    # TODO: Check for common RSS paths/etc. and parse accordingly.
    #       Maybe check for common domains and handle some appropriately

    return "Other sites are not supported yet. Skipping..."


# Pull the list of contributors from the YAML file in our repo.
try:
    response = requests.get(repo_url)
    data = yaml.safe_load(response.text)
    print("-" * 16 + " Start YAML data " + "-" * 16)
    print(data)
    print("\n")
    repos = data["members"]
    print(repos)

except:
    print("Could not get the repos. Check the YAML file exists and is valid.")
    repos = None

if repos != None:
    # TODO: - Check list of members remote posts against their posts in the DB.
    #       - Delete any DB posts that aren't in remote posts, and add any new posts.
    # TODO: - Figure out a way to check for changes in posts without having to re-pull all post contents and DIFF'ing.

    for repo in repos:
        for username, details in repo.items():
            print("-=" * 32)
            output = ""

            name = details["name"]
            website = details["website"]
            posts_url = details["posts"]

            output += f"Processing  {name}'s posts from {website}:\n"
            output += f"Posts source: {posts_url}\n"

            print(output)

            # Check for "github" or "gitlab" in the posts URL
            if "github.com" in posts_url.lower():
                posts = get_github(username, posts_url)
            elif "gitlab.com" in posts_url.lower():
                posts = get_gitlab(username, posts_url)
            else:
                posts = get_other(username, posts_url)

            if isinstance(posts, list):
                for post in posts:
                    print(f"Processing: {post}")
            else:
                # It's assumed to be a string (an error message or some other message)
                print(posts)

    # return output.replace("\n", "<br>")  # Return HTML line breaks for web display
