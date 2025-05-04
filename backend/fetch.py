# -*- coding: utf-8 -*-
import requests
import json
import os
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple, Any
from dotenv import load_dotenv
import time

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_VERSION = "2022-11-28"
API_BASE_URL = "https://api.github.com"
COMMIT_MESSAGE_MAX_LEN = 100

# --- !! NEW: Commit Detail Limit !! ---
# Set the maximum number of commit *detail* API calls per repository.
# Useful for testing or avoiding excessive rate limit usage.
# Set to None to fetch details for all commits found in the initial list.
# Set to e.g., 3 to only fetch details for the first 3 commits per repo.
MAX_COMMITS_TO_DETAIL_PER_REPO = 3 # <-- SET YOUR LIMIT HERE FOR TESTING

# --- Helper Functions ---
# (parse_github_url, make_github_request, fetch_paginated_data - include full code from previous version)
def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Parses a GitHub repository URL to extract owner and repo name."""
    try:
        parsed = urlparse(url)
        if parsed.netloc.lower() != 'github.com':
            print(f"Warning: URL '{url}' is not a standard GitHub URL.")
            return None
        path_parts = [part for part in parsed.path.strip('/').split('/') if part]
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            if repo.endswith('.git'): repo = repo[:-4]
            return owner, repo
        else:
            print(f"Warning: Could not parse owner/repo from URL '{url}'. Path: {parsed.path}")
            return None
    except Exception as e:
        print(f"Error parsing URL '{url}': {e}")
        return None

def make_github_request(url: str, token: Optional[str], params: Optional[Dict] = None) -> Optional[requests.Response]:
    """Makes a request to the GitHub API with headers and error handling."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if token: headers["Authorization"] = f"Bearer {token}"
    retries = 2
    while retries >= 0:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and int(response.headers['X-RateLimit-Remaining']) == 0:
                if retries > 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                    wait_time = max(0, reset_time - time.time()) + 5
                    print(f"Rate limit hit requesting {url}. Waiting for {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    retries -= 1
                    continue
                else:
                    print(f"Rate limit hit, and no retries left for {url}.")
                    response.raise_for_status()
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if response is not None:
                status_code = response.status_code
                if status_code == 404: print(f"Error: Resource not found (404) for URL: {url}")
                elif status_code == 403: print(f"Error: Forbidden (403) for URL: {url}. Check token permissions.")
                elif status_code == 204: print(f"Info: No content (204) for URL: {url}"); return response
                elif status_code == 409: print(f"Info: Conflict (409) for URL: {url}. Repo might be empty."); return None
                elif status_code == 422: print(f"Error: Unprocessable Entity (422) for URL: {url}. Invalid input?"); return None
                elif status_code >= 500: print(f"Server Error ({status_code}) for URL: {url}. Retrying might help later."); return None
                else: print(f"HTTP Error fetching {url}: {e} (Status code: {status_code})")
            else: print(f"HTTP Error occurred before response object was created for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Network Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during request to {url}: {e}")
            return None
        break

def fetch_paginated_data(url: str, token: Optional[str], params: Optional[Dict] = None) -> Optional[List[Dict[str, Any]]]:
    """Fetches paginated data from a GitHub API endpoint."""
    all_data = []
    page = 1
    current_url = url
    if params is None: params = {}
    while current_url:
        request_params = params if page == 1 else None
        # print(f"Fetching data from {current_url} (Page {page})...") # Less verbose logging
        response = make_github_request(current_url, token, request_params)
        if response is None: return None
        if response.status_code == 204: break
        try:
            if not response.content: break
            page_data = response.json()
            if not isinstance(page_data, list): break
            if not page_data: break
            all_data.extend(page_data)
            if 'next' in response.links:
                 current_url = response.links['next']['url']
                 page += 1
                 time.sleep(0.2)
            else: current_url = None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {current_url}: {e}")
            return None
        except Exception as e:
             print(f"Error processing page {page} from {current_url}: {e}")
             return None
    # print(f"Successfully fetched {len(all_data)} items total from base URL {url}.") # Less verbose logging
    return all_data

def fetch_contributors_from_repo(owner: str, repo: str, token: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Fetches the list of contributors for a specific repository."""
    contributors_url = f"{API_BASE_URL}/repos/{owner}/{repo}/contributors"
    print(f"Fetching contributors for {owner}/{repo}...")
    return fetch_paginated_data(contributors_url, token, {"per_page": 100})

def fetch_repository_issues(owner: str, repo: str, token: Optional[str] = None, state: str = "closed") -> Optional[List[Dict[str, Any]]]:
    """Fetches issues for a specific repository, filtering by state."""
    issues_url = f"{API_BASE_URL}/repos/{owner}/{repo}/issues"
    params = {"state": state, "per_page": 100}
    print(f"Fetching '{state}' issues for {owner}/{repo}...")
    return fetch_paginated_data(issues_url, token, params)

def fetch_repository_commits(owner: str, repo: str, token: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Fetches commit summaries for a specific repository."""
    commits_url = f"{API_BASE_URL}/repos/{owner}/{repo}/commits"
    params = {"per_page": 100}
    print(f"Fetching commit summaries for {owner}/{repo}...")
    return fetch_paginated_data(commits_url, token, params)

def fetch_commit_details(owner: str, repo: str, commit_sha: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches detailed information for a single commit."""
    commit_url = f"{API_BASE_URL}/repos/{owner}/{repo}/commits/{commit_sha}"
    # Logging moved to process_repositories to include limit info
    response = make_github_request(commit_url, token)
    if response and response.status_code == 200:
        try:
            details = response.json()
            time.sleep(0.4) # Pace the detail requests
            return details
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for commit details {commit_sha}: {e}")
            return None
    else:
        # Error logged in make_github_request
        return None

# --- MODIFIED FUNCTION ---
def process_repositories(repo_urls: List[str], token: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetches contributors, their assigned closed issues, and detailed commit info
    (up to a limit per repo) for multiple repositories. Merges the data.
    Returns a dictionary of unique contributors keyed by username.
    """
    all_contributors_map: Dict[str, Dict[str, Any]] = {}

    for repo_url in repo_urls:
        print(f"\n--- Processing repository: {repo_url} ---")
        parsed_info = parse_github_url(repo_url)
        if not parsed_info: continue
        owner, repo = parsed_info
        canonical_repo_url = f"https://github.com/{owner}/{repo}"

        # Step 1: Fetch Contributors
        repo_contributors = fetch_contributors_from_repo(owner, repo, token)
        if repo_contributors is None: repo_contributors = []
        for contributor_data in repo_contributors:
            required_keys = ['login', 'id', 'html_url', 'avatar_url']
            if not all(k in contributor_data for k in required_keys) or contributor_data.get('type') != 'User': continue
            username = contributor_data['login']
            if username not in all_contributors_map: all_contributors_map[username] = {"id": contributor_data['id'], "username": username, "url": contributor_data['html_url'], "avatar_url": contributor_data['avatar_url'], "works": []}
            if 'works' not in all_contributors_map[username]: all_contributors_map[username]['works'] = []

        # Step 2: Fetch and Process Closed Issues
        repo_closed_issues = fetch_repository_issues(owner, repo, token, state="closed")
        issues_assigned_to_user_in_repo: Dict[str, List[Dict]] = {}
        assignee_details_cache: Dict[str, Dict] = {}
        if repo_closed_issues:
            for issue_data in repo_closed_issues:
                if 'pull_request' in issue_data or issue_data.get('state') != 'closed': continue
                assignees = issue_data.get('assignees', []) or ([issue_data['assignee']] if issue_data.get('assignee') else [])
                if not assignees: continue
                simplified_issue = {"url": issue_data.get('html_url', ''), "title": issue_data.get('title', 'No Title')}
                if not simplified_issue["url"]: continue
                for assignee in assignees:
                    if assignee and isinstance(assignee, dict) and 'login' in assignee:
                        assignee_username = assignee['login']
                        if assignee_username not in issues_assigned_to_user_in_repo: issues_assigned_to_user_in_repo[assignee_username] = []
                        if not any(i['url'] == simplified_issue['url'] for i in issues_assigned_to_user_in_repo[assignee_username]): issues_assigned_to_user_in_repo[assignee_username].append(simplified_issue)
                        if assignee_username not in all_contributors_map and assignee_username not in assignee_details_cache: assignee_details_cache[assignee_username] = {"id": assignee.get('id'), "url": assignee.get('html_url'), "avatar_url": assignee.get('avatar_url')}
        else: print(f"No closed issues found or fetch failed for {owner}/{repo}.")

        # --- Step 3: Fetch and Process Commits (with Details Limit) ---
        repo_commits_list = fetch_repository_commits(owner, repo, token)
        commits_authored_by_user_in_repo: Dict[str, List[Dict]] = {}
        author_details_cache: Dict[str, Dict] = {}
        commits_detailed_count = 0 # Counter for detail calls *per repository*

        if repo_commits_list:
            print(f"Fetched {len(repo_commits_list)} commit summaries. Processing details (limit per repo: {MAX_COMMITS_TO_DETAIL_PER_REPO})...")
            for commit_summary_data in repo_commits_list:
                commit_sha = commit_summary_data.get('sha')
                if not commit_sha: continue

                commit_author_info = commit_summary_data.get('author')
                if not commit_author_info or not isinstance(commit_author_info, dict) or 'login' not in commit_author_info: continue
                author_username = commit_author_info['login']

                # --- Prepare Basic Commit Info ---
                commit_message = commit_summary_data.get('commit', {}).get('message', 'No commit message')
                commit_message_summary = commit_message.split('\n', 1)[0]
                if len(commit_message_summary) > COMMIT_MESSAGE_MAX_LEN:
                     commit_message_summary = commit_message_summary[:COMMIT_MESSAGE_MAX_LEN] + '...'

                simplified_commit = {
                    "sha": commit_sha,
                    "url": commit_summary_data.get('html_url', ''),
                    "message": commit_message_summary,
                    # Initialize detailed fields to None/default
                    "stats": None,
                    "files_changed": [],
                    "comment_count": 0,
                    "diff_patch": None # New field for code changes
                }
                if not simplified_commit["url"]: continue

                # --- Check Limit and Fetch Details ---
                should_fetch_details = (
                    MAX_COMMITS_TO_DETAIL_PER_REPO is None or
                    commits_detailed_count < MAX_COMMITS_TO_DETAIL_PER_REPO
                )
                detailed_commit_data = None # Reset for each commit
                if should_fetch_details:
                    limit_str = f"{MAX_COMMITS_TO_DETAIL_PER_REPO}" if MAX_COMMITS_TO_DETAIL_PER_REPO is not None else "unlimited"
                    print(f"  [{commits_detailed_count + 1}/{limit_str}] Fetching details for commit {commit_sha[:7]}...")
                    detailed_commit_data = fetch_commit_details(owner, repo, commit_sha, token)
                    commits_detailed_count += 1 # Increment *only* if detail fetch was attempted
                # else: # Optional: Log skipped commits
                    # print(f"  Skipping detail fetch for commit {commit_sha[:7]} (limit reached).")

                # --- Populate with Detailed Info if available ---
                if detailed_commit_data:
                    stats = detailed_commit_data.get('stats')
                    files = detailed_commit_data.get('files', [])
                    comment_count = detailed_commit_data.get('commit', {}).get('comment_count', 0)

                    simplified_commit["stats"] = stats
                    simplified_commit["comment_count"] = comment_count
                    simplified_commit["files_changed"] = [
                        {"filename": f.get('filename'), "status": f.get('status')}
                        for f in files if f.get('filename')
                    ]

                    # --- Extract Patch/Diff ---
                    combined_patch = ""
                    for f in files:
                        # Check if 'patch' key exists and has content
                        if 'patch' in f and isinstance(f['patch'], str) and f['patch']:
                            combined_patch += f"--- File: {f.get('filename', 'Unknown')} ---\n"
                            combined_patch += f['patch']
                            combined_patch += "\n\n" # Separator between file patches
                    # Add the combined patch string if any patches were found
                    simplified_commit["diff_patch"] = combined_patch.strip() if combined_patch else None
                # If detailed_commit_data is None (fetch failed or limit reached),
                # the simplified_commit retains its basic info and None/default details.

                # Add commit (basic or detailed) to the user's list for this repo
                if author_username not in commits_authored_by_user_in_repo:
                    commits_authored_by_user_in_repo[author_username] = []
                if not any(c['sha'] == simplified_commit['sha'] for c in commits_authored_by_user_in_repo[author_username]):
                    commits_authored_by_user_in_repo[author_username].append(simplified_commit)

                # Cache author details if needed
                if author_username not in all_contributors_map and author_username not in author_details_cache:
                     author_details_cache[author_username] = {"id": commit_author_info.get('id'), "url": commit_author_info.get('html_url'), "avatar_url": commit_author_info.get('avatar_url')}
        else:
             print(f"No commit summaries found or fetch failed for {owner}/{repo}.")

        # --- Step 4: Integrate Issues and Commits into Contributor Works ---
        involved_users = set(all_contributors_map.keys()) | set(issues_assigned_to_user_in_repo.keys()) | set(commits_authored_by_user_in_repo.keys())
        for username in involved_users:
            if username not in all_contributors_map:
                details = assignee_details_cache.get(username) or author_details_cache.get(username) or {}
                print(f"Adding contributor '{username}' based on activity in {owner}/{repo}.")
                all_contributors_map[username] = {"id": details.get('id'), "username": username, "url": details.get('url'), "avatar_url": details.get('avatar_url'), "works": []}

            contributor_works = all_contributors_map[username]['works']
            repo_work_entry = next((work for work in contributor_works if work.get("repository_url") == canonical_repo_url), None)

            if repo_work_entry is None:
                repo_work_entry = {
                    "repository_url": canonical_repo_url,
                    "issues": issues_assigned_to_user_in_repo.get(username, []),
                    "commits": commits_authored_by_user_in_repo.get(username, [])
                }
                contributor_works.append(repo_work_entry)
            else:
                 repo_work_entry["issues"] = issues_assigned_to_user_in_repo.get(username, repo_work_entry.get("issues", []))
                 repo_work_entry["commits"] = commits_authored_by_user_in_repo.get(username, repo_work_entry.get("commits", []))

    return all_contributors_map

# --- Main Execution ---
if __name__ == "__main__":
    repository_urls = [
        "https://github.com/MrCogito/setra_hackaton",
        "https://github.com/meta-llama/llama-prompt-ops"
    ]

    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not found.")
        print("API requests will be unauthenticated and subject to much lower rate limits.")
        print("Fetching commit details without a token is highly likely to fail or be severely limited.")
    else:
        print("Successfully loaded GITHUB_TOKEN from environment.")

    # Explain the commit detail limit being used
    if MAX_COMMITS_TO_DETAIL_PER_REPO is not None:
        print(f"--- NOTE: Will attempt to fetch details for a maximum of {MAX_COMMITS_TO_DETAIL_PER_REPO} commits per repository ---")
        print("--- Commits beyond this limit will only have basic info (sha, url, message) ---")
    else:
        print("--- NOTE: Attempting to fetch details for ALL found commits per repository (can be very slow and API intensive) ---")


    start_time = time.time()
    contributors_map = process_repositories(repository_urls, GITHUB_TOKEN)
    end_time = time.time()

    final_contributor_list = list(contributors_map.values())

    output_data = {
        "contributors": final_contributor_list
    }

    print(f"\n--- Processing completed in {end_time - start_time:.2f} seconds ---")

    print("\n--- Final Combined Contributor Data (JSON) ---")

    # Save to a file is highly recommended due to potential size
    output_filename = "github_contributors_detailed_commits_limited.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully saved data to {output_filename}")
        # Optionally print a small part if needed for quick verification
        # print("\n--- Sample Output (First Contributor) ---")
        # if final_contributor_list:
        #     print(json.dumps(final_contributor_list[0], indent=2, ensure_ascii=False))
        # else:
        #     print("No contributors found.")

    except IOError as e:
        print(f"\nError saving data to file: {e}")
    except TypeError as e:
         print(f"\nError serializing data to JSON: {e}")