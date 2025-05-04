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

# Set the maximum number of commit *detail* API calls per repository.
MAX_COMMITS_TO_DETAIL_PER_REPO = 3 # Set to None to fetch details for all

# --- Helper Functions ---
# (Include the full code for parse_github_url, make_github_request, fetch_paginated_data here)
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
                    response.raise_for_status() # Raise here to signal failure after retries
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if response is not None:
                status_code = response.status_code
                if status_code == 404: print(f"Error: Resource not found (404) for URL: {url}")
                elif status_code == 403: print(f"Error: Forbidden (403) for URL: {url}. Check token permissions or rate limits.")
                elif status_code == 204: print(f"Info: No content (204) for URL: {url}"); return response
                elif status_code == 409: print(f"Info: Conflict (409) for URL: {url}. Repo might be empty."); return None
                elif status_code == 422: print(f"Error: Unprocessable Entity (422) for URL: {url}. Invalid input?"); return None
                elif status_code >= 500: print(f"Server Error ({status_code}) for URL: {url}. Retrying might help later."); return None
                else: print(f"HTTP Error fetching {url}: {e} (Status code: {status_code})")
            else: print(f"HTTP Error occurred before response object was created for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Network Error fetching {url}: {e}")
            if retries > 0:
                print("Retrying after network error...")
                time.sleep(5) # Wait before retrying network errors
                retries -= 1
                continue
            else:
                print("Network error persisted after retries.")
                return None
        except Exception as e:
            print(f"An unexpected error occurred during request to {url}: {e}")
            return None
    return None # Should be unreachable if retries exhausted, but added for safety

def fetch_paginated_data(url: str, token: Optional[str], params: Optional[Dict] = None) -> Optional[List[Dict[str, Any]]]:
    """Fetches paginated data from a GitHub API endpoint."""
    all_data = []
    page = 1
    current_url = url
    # Apply initial params only to the first request
    request_params = params.copy() if params else {}
    request_params['page'] = page

    while current_url:
        print(f"  Fetching page {page} from {current_url.split('?')[0]}...") # Log base URL
        response = make_github_request(current_url, token, request_params)

        # Reset params for subsequent requests using 'next' link URL
        request_params = None

        if response is None: return None # Request failed
        if response.status_code == 204: break # No content

        try:
            # Check for empty content before attempting JSON decode
            if not response.content:
                print(f"  Warning: Received empty response body from {current_url}.")
                break

            page_data = response.json()

            # Handle cases where the response isn't a list (e.g., error object)
            if not isinstance(page_data, list):
                 print(f"  Warning: Expected a list but received type {type(page_data)} from {current_url}. Content: {response.text[:100]}...")
                 # If it looks like an error message, stop pagination
                 if isinstance(page_data, dict) and ('message' in page_data or 'errors' in page_data):
                      print(f"  Error message detected, stopping pagination.")
                      return None if not all_data else all_data # Return what we have if some pages worked
                 break # Otherwise, just stop processing this page

            if not page_data: break # Empty list means no more data

            all_data.extend(page_data)

            # Process 'next' link
            if 'next' in response.links:
                 current_url = response.links['next']['url']
                 page += 1
                 # Small delay between pages to be polite to the API
                 time.sleep(0.3) # Increased slightly
            else:
                 current_url = None # No more pages

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {current_url or url}: {e}. Response text: {response.text[:200]}")
            # Don't necessarily fail everything if one page fails to decode, return what we got
            return all_data if all_data else None
        except Exception as e:
             print(f"Error processing page {page} from {current_url or url}: {e}")
             # Return what we have so far
             return all_data if all_data else None

    print(f"  Finished fetching paginated data, total items: {len(all_data)}")
    return all_data


# --- Functions to Fetch Data ---
def fetch_contributors_from_repo(owner: str, repo: str, token: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Fetches the list of contributors for a specific repository."""
    contributors_url = f"{API_BASE_URL}/repos/{owner}/{repo}/contributors"
    print(f"Fetching contributors for {owner}/{repo}...")
    return fetch_paginated_data(contributors_url, token, {"per_page": 100, "anon": "false"}) # Explicitly exclude anonymous

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
    # print(f"    Fetching details for commit {commit_sha[:7]}...") # Moved logging up
    response = make_github_request(commit_url, token)
    if response and response.status_code == 200:
        try:
            details = response.json()
            time.sleep(0.5) # Slightly increased delay after successful detail fetch
            return details
        except json.JSONDecodeError as e:
            print(f"    Error decoding JSON for commit details {commit_sha}: {e}")
            return None
    else:
        # Error message already printed by make_github_request
        return None

# --- MODIFIED FUNCTION ---
def process_repositories(repo_urls: List[str], token: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetches contributors, their assigned closed issues, and detailed commit info
    (up to a limit per repo, excluding stats) for multiple repositories. Merges the data.
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
        if repo_contributors is None: repo_contributors = [] # Treat fetch failure as empty list
        for contributor_data in repo_contributors:
            # Ensure required keys are present and it's a User (not Bot)
            required_keys = ['login', 'id', 'html_url', 'avatar_url']
            if not all(k in contributor_data for k in required_keys) or contributor_data.get('type') != 'User': continue
            username = contributor_data['login']
            if not username: continue # Skip if login is somehow empty

            # Initialize contributor in the main map if not present
            if username not in all_contributors_map:
                all_contributors_map[username] = {
                    "id": contributor_data['id'],
                    "username": username,
                    "url": contributor_data['html_url'],
                    "avatar_url": contributor_data['avatar_url'],
                    "works": [] # Initialize works list
                 }
            # Ensure 'works' list exists even if user was added previously without it
            all_contributors_map[username].setdefault('works', [])

        # Step 2: Fetch and Process Closed Issues
        repo_closed_issues = fetch_repository_issues(owner, repo, token, state="closed")
        issues_assigned_to_user_in_repo: Dict[str, List[Dict]] = {}
        assignee_details_cache: Dict[str, Dict] = {} # Cache details for users found only via issues

        if repo_closed_issues:
            print(f"Processing {len(repo_closed_issues)} fetched closed issues...")
            for issue_data in repo_closed_issues:
                # Skip pull requests and issues not actually closed
                if 'pull_request' in issue_data or issue_data.get('state') != 'closed': continue

                # Handle both 'assignees' list and legacy 'assignee' field
                assignees_list = issue_data.get('assignees', [])
                if not assignees_list and issue_data.get('assignee'):
                    assignees_list = [issue_data['assignee']]

                if not assignees_list: continue # Skip issue if no assignees

                simplified_issue = {"url": issue_data.get('html_url'), "title": issue_data.get('title', 'No Title')}
                if not simplified_issue["url"] or not simplified_issue["title"]: continue # Skip if essential info missing

                for assignee in assignees_list:
                    # Validate assignee data
                    if assignee and isinstance(assignee, dict) and 'login' in assignee and assignee.get('type') == 'User':
                        assignee_username = assignee['login']
                        if not assignee_username: continue # Skip if login is empty

                        # Add issue to this user's list for this repo
                        if assignee_username not in issues_assigned_to_user_in_repo:
                            issues_assigned_to_user_in_repo[assignee_username] = []
                        # Avoid adding duplicate issue URLs
                        if not any(i['url'] == simplified_issue['url'] for i in issues_assigned_to_user_in_repo[assignee_username]):
                            issues_assigned_to_user_in_repo[assignee_username].append(simplified_issue)

                        # Cache assignee details if they are not already in the main map
                        if assignee_username not in all_contributors_map and assignee_username not in assignee_details_cache:
                            assignee_details_cache[assignee_username] = {
                                "id": assignee.get('id'),
                                "url": assignee.get('html_url'),
                                "avatar_url": assignee.get('avatar_url')
                            }
        else:
            print(f"No closed issues found or fetch failed for {owner}/{repo}.")

        # --- Step 3: Fetch and Process Commits (with Details Limit, No Stats) ---
        repo_commits_list = fetch_repository_commits(owner, repo, token)
        commits_authored_by_user_in_repo: Dict[str, List[Dict]] = {}
        author_details_cache: Dict[str, Dict] = {} # Cache details for users found only via commits
        commits_detailed_count = 0

        if repo_commits_list:
            print(f"Processing {len(repo_commits_list)} fetched commit summaries. Fetching details (limit per repo: {MAX_COMMITS_TO_DETAIL_PER_REPO})...")
            for commit_summary_data in repo_commits_list:
                commit_sha = commit_summary_data.get('sha')
                if not commit_sha: continue

                # Use 'author' field for GitHub user linking (committer might be different)
                # Ensure author exists, is a dict, has login, and is a User
                commit_author_info = commit_summary_data.get('author')
                if not commit_author_info or not isinstance(commit_author_info, dict) \
                   or 'login' not in commit_author_info or commit_author_info.get('type') != 'User':
                   # Fallback or log if needed, e.g., using commit.author.name/email if no GitHub user
                   # print(f"  Skipping commit {commit_sha[:7]} due to missing or invalid author info.")
                   continue # Skip commits without a valid GitHub author

                author_username = commit_author_info['login']
                if not author_username: continue # Skip if login is empty

                # Prepare Basic Commit Info
                commit_message = commit_summary_data.get('commit', {}).get('message', 'No commit message')
                commit_message_summary = commit_message.split('\n', 1)[0] # First line only
                if len(commit_message_summary) > COMMIT_MESSAGE_MAX_LEN:
                     commit_message_summary = commit_message_summary[:COMMIT_MESSAGE_MAX_LEN - 3] + '...' # Adjust slicing

                simplified_commit = {
                    "sha": commit_sha,
                    "url": commit_summary_data.get('html_url'),
                    "message": commit_message_summary,
                    # Initialize detailed fields (NO stats)
                    "files_changed": None, # Use None to indicate details not fetched/available
                    "comment_count": None,
                    "diff_patch": None
                }
                if not simplified_commit["url"]: continue # Skip if essential info missing

                # Check Limit and Fetch Details
                should_fetch_details = (
                    MAX_COMMITS_TO_DETAIL_PER_REPO is None or
                    commits_detailed_count < MAX_COMMITS_TO_DETAIL_PER_REPO
                )
                detailed_commit_data = None
                if should_fetch_details:
                    limit_str = f"{MAX_COMMITS_TO_DETAIL_PER_REPO}" if MAX_COMMITS_TO_DETAIL_PER_REPO is not None else "all"
                    print(f"  [{commits_detailed_count + 1}/{limit_str}] Fetching details for commit {commit_sha[:7]} by {author_username}...")
                    detailed_commit_data = fetch_commit_details(owner, repo, commit_sha, token)
                    if detailed_commit_data: # Only increment if fetch was successful
                         commits_detailed_count += 1
                    else:
                         print(f"    Failed to fetch details for commit {commit_sha[:7]}.")


                # Populate with Detailed Info if available (NO stats)
                if detailed_commit_data:
                    files = detailed_commit_data.get('files', [])
                    # Ensure commit object and comment_count exist before accessing
                    commit_details_commit_obj = detailed_commit_data.get('commit', {})
                    comment_count = commit_details_commit_obj.get('comment_count', 0) if commit_details_commit_obj else 0

                    simplified_commit["comment_count"] = comment_count
                    simplified_commit["files_changed"] = [
                        {"filename": f.get('filename'), "status": f.get('status')}
                        for f in files if f.get('filename') # Ensure filename exists
                    ] if files else [] # Handle case where files list might be missing or empty

                    # Extract Patch/Diff if files exist
                    combined_patch = ""
                    if files:
                         for f in files:
                            # Check if 'patch' exists, is a string, and is not empty
                             if f and 'patch' in f and isinstance(f.get('patch'), str) and f['patch']:
                                 combined_patch += f"--- File: {f.get('filename', 'Unknown')} ---\n"
                                 combined_patch += f['patch']
                                 combined_patch += "\n\n"
                    simplified_commit["diff_patch"] = combined_patch.strip() if combined_patch else None # Use None if no patch data

                # Add commit (basic or detailed) to the user's list for this repo
                if author_username not in commits_authored_by_user_in_repo:
                    commits_authored_by_user_in_repo[author_username] = []
                 # Avoid adding duplicate commit SHAs
                if not any(c['sha'] == simplified_commit['sha'] for c in commits_authored_by_user_in_repo[author_username]):
                     commits_authored_by_user_in_repo[author_username].append(simplified_commit)

                # Cache author details if they are not already in the main map
                if author_username not in all_contributors_map and author_username not in author_details_cache:
                     author_details_cache[author_username] = {
                         "id": commit_author_info.get('id'),
                         "url": commit_author_info.get('html_url'),
                         "avatar_url": commit_author_info.get('avatar_url')
                     }
        else:
             print(f"No commit summaries found or fetch failed for {owner}/{repo}.")

        # --- Step 4: Integrate Issues and Commits into Contributor Works ---
        # Identify all users involved in this repo (contributors + assignees + authors)
        involved_users_in_repo = set()
        if repo_contributors: involved_users_in_repo.update(c['login'] for c in repo_contributors if c.get('login'))
        involved_users_in_repo.update(issues_assigned_to_user_in_repo.keys())
        involved_users_in_repo.update(commits_authored_by_user_in_repo.keys())

        print(f"Integrating activities for {len(involved_users_in_repo)} users in {owner}/{repo}...")

        for username in involved_users_in_repo:
            # Ensure user exists in the main map, adding them if necessary using cached details
            if username not in all_contributors_map:
                details = assignee_details_cache.get(username) or author_details_cache.get(username)
                if details and (details.get('id') or details.get('url')): # Check if we have some usable details
                    print(f"Adding contributor '{username}' based on activity in {owner}/{repo}.")
                    all_contributors_map[username] = {
                        "id": details.get('id'),
                        "username": username,
                        "url": details.get('url'),
                        "avatar_url": details.get('avatar_url'),
                        "works": [] # Initialize works
                    }
                else:
                    print(f"Warning: Skipping user '{username}' found via activity in {owner}/{repo} as details couldn't be retrieved or cached.")
                    continue # Skip this user if we have no details

            # Ensure 'works' list exists for the user
            contributor_works = all_contributors_map[username].setdefault('works', [])

            # Get the specific contributions for THIS user in THIS repo
            user_issues_in_repo = issues_assigned_to_user_in_repo.get(username, [])
            user_commits_in_repo = commits_authored_by_user_in_repo.get(username, [])

            # *** KEY CHANGE: Only add/update repo entry if there are actual contributions ***
            if user_issues_in_repo or user_commits_in_repo:
                # Find if an entry for this repo already exists for the user
                repo_work_entry = next((work for work in contributor_works if work.get("repository_url") == canonical_repo_url), None)

                if repo_work_entry is None:
                    # Create a NEW entry because it doesn't exist and there's activity
                    repo_work_entry = {
                        "repository_url": canonical_repo_url,
                        "issues": user_issues_in_repo,
                        "commits": user_commits_in_repo
                    }
                    contributor_works.append(repo_work_entry)
                    # print(f"  Added new repo entry for {username} in {owner}/{repo}")
                else:
                    # Update existing entry for this repo (less likely needed with current flow, but safe)
                    # Overwrite lists with the latest fetched data for this repo pass
                    repo_work_entry["issues"] = user_issues_in_repo
                    repo_work_entry["commits"] = user_commits_in_repo
                    # print(f"  Updated existing repo entry for {username} in {owner}/{repo}")
            # else:
                # If both lists are empty, do nothing - no entry is added or modified for this repo.
                # print(f"  Skipping empty repo entry for {username} in {owner}/{repo}")


    return all_contributors_map

# --- Main Execution ---
if __name__ == "__main__":
    repository_urls = [
        "https://github.com/meta-llama/llama-stack-apps",
        "https://github.com/meta-llama/llama-prompt-ops"
    ]

    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not found.")
        print("API requests will be unauthenticated and subject to much lower rate limits.")
        print("Fetching commit details without a token is highly likely to fail or be severely limited.")
    else:
        # Simple check if token seems valid (starts with ghp_ or ghu_)
        if GITHUB_TOKEN.startswith("ghp_") or GITHUB_TOKEN.startswith("ghu_"):
             print("Successfully loaded GITHUB_TOKEN from environment.")
        else:
             print("Warning: GITHUB_TOKEN loaded, but doesn't look like a standard Personal Access Token.")


    if MAX_COMMITS_TO_DETAIL_PER_REPO is not None:
        print(f"--- NOTE: Will attempt to fetch details (excluding stats) for a maximum of {MAX_COMMITS_TO_DETAIL_PER_REPO} commits per repository ---")
        print("--- Commits beyond this limit will only have basic info (sha, url, message) ---")
    else:
        print("--- NOTE: Attempting to fetch details (excluding stats) for ALL found commits per repository (can be very slow and API intensive) ---")

    start_time = time.time()
    contributors_map = process_repositories(repository_urls, GITHUB_TOKEN)
    end_time = time.time()

    # Convert the map to a list for the final output
    final_contributor_list = list(contributors_map.values())

    # Optional: Sort contributors by username
    final_contributor_list.sort(key=lambda x: x.get('username', '').lower())

    output_data = {
        "contributors": final_contributor_list
        # Maybe add some metadata like processing time, repos processed?
        # "metadata": {
        #    "processed_repos": repository_urls,
        #    "processing_time_seconds": round(end_time - start_time, 2),
        #    "commit_detail_limit_per_repo": MAX_COMMITS_TO_DETAIL_PER_REPO
        # }
    }

    print(f"\n--- Processing completed in {end_time - start_time:.2f} seconds ---")
    print(f"--- Found data for {len(final_contributor_list)} unique contributors across processed repositories ---")


    output_filename = "github_contributors_detailed_commits_no_stats_v2.json"
    try:
        print(f"\nAttempting to save data to {output_filename}...")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved data to {output_filename}")
    except IOError as e:
        print(f"\nError saving data to file '{output_filename}': {e}")
    except TypeError as e:
         print(f"\nError serializing data to JSON: {e}")
         # Optionally print a snippet of the data causing issues
         # print("Problematic data snippet (first contributor):")
         # print(json.dumps(output_data['contributors'][0] if output_data['contributors'] else {}, indent=2, ensure_ascii=False))

    # Optional: Print summary of users with no works (might indicate issues or just inactive users)
    users_with_no_works = [c['username'] for c in final_contributor_list if not c.get('works')]
    if users_with_no_works:
        print(f"\nNote: {len(users_with_no_works)} contributors were identified but had no associated closed issues or commits recorded in the processed repositories:")
        # print(f"  {', '.join(users_with_no_works[:10])}{'...' if len(users_with_no_works) > 10 else ''}")