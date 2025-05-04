import os
import sys
import json
from urllib.parse import urlparse

# --- Django Setup ---
# Add the project root directory (backend) to the Python path
# Adjust the number of '..' based on where populate.py is relative to manage.py
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Set the DJANGO_SETTINGS_MODULE environment variable
# Replace 'backend.settings' with your actual settings file path if different
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
# --- End Django Setup ---

# Now import models AFTER django.setup()
from api.models import Contributor, Repository, Issue, Commit, RepositoryWork

# --- Configuration ---
JSON_FILE_PATH = 'github_contributors_detailed_commits_no_stats.json' # Path to your generated JSON

def parse_repo_name_from_url(url: str) -> str:
    """Extracts 'owner/repo' from a GitHub repository URL."""
    try:
        path = urlparse(url).path.strip('/')
        parts = path.split('/')
        if len(parts) >= 2:
            # Return owner/repo format
            return f"{parts[0]}/{parts[1]}"
        else:
            # Fallback if URL format is unexpected
            return path # Or raise an error, or return None
    except Exception:
        return url # Fallback to the full URL if parsing fails

def populate_database(json_file_path: str):
    """Loads data from JSON and populates the Django database."""
    print(f"Loading data from {json_file_path}...")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file_path}'")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_file_path}'")
        sys.exit(1)

    contributors_data = data.get('contributors', [])
    if not contributors_data:
        print("No contributors found in the JSON data.")
        return

    print(f"Found {len(contributors_data)} contributors. Starting population...")

    processed_count = 0
    for contributor_info in contributors_data:
        username = contributor_info.get('username')
        if not username:
            print("Skipping contributor with missing username.")
            continue

        # --- Create or Get Contributor ---
        contributor, created = Contributor.objects.get_or_create(
            username=username,
            defaults={
                'url': contributor_info.get('url', ''),
                'avatar_url': contributor_info.get('avatar_url', ''),
                'summary': contributor_info.get('summary', '') # Assuming summary might be added later
            }
        )
        if created:
            print(f"  Created Contributor: {username}")
        else:
            # Optionally update existing contributors if needed
            # contributor.url = contributor_info.get('url', contributor.url)
            # contributor.avatar_url = contributor_info.get('avatar_url', contributor.avatar_url)
            # contributor.save()
            print(f"  Found Contributor: {username}")

        # --- Process Works ---
        works_data = contributor_info.get('works', [])
        for work_info in works_data:
            repo_url = work_info.get('repository_url')
            if not repo_url:
                print(f"    Skipping work entry for {username} due to missing repository URL.")
                continue

            repo_name = parse_repo_name_from_url(repo_url)

            # --- Create or Get Repository ---
            # Note: Repository model currently lacks avatar_url and summary from source JSON
            repository, repo_created = Repository.objects.get_or_create(
                url=repo_url,
                defaults={
                    'name': repo_name,
                    'avatar_url': '', # Not available in current JSON structure for repo
                    'summary': ''     # Not available in current JSON structure for repo
                }
            )
            if repo_created:
                print(f"      Created Repository: {repo_name}")
            # else: # Optionally update repo name if URL somehow changed but points to same logical repo
            #     if repository.name != repo_name:
            #         repository.name = repo_name
            #         repository.save()

            # --- Create or Get RepositoryWork ---
            # This links the specific repository to the work done within it
            # The link to the contributor happens via contributor.works.add() later
            repo_work, work_created = RepositoryWork.objects.get_or_create(
                repository=repository
                # Add defaults if RepositoryWork has other unique fields or required data
                # defaults={'summary': f"Work in {repo_name}"} # Example summary
            )
            if work_created:
                 print(f"        Created RepositoryWork link for {repo_name}")

            # --- Process Issues ---
            issues_data = work_info.get('issues', [])
            for issue_info in issues_data:
                issue_url = issue_info.get('url')
                if not issue_url: continue

                issue_title = issue_info.get('title', 'No Title')
                # Prepare raw_data for Issue (just title for now, as requested)
                issue_raw = {'title': issue_title}

                issue_obj, issue_created = Issue.objects.get_or_create(
                    url=issue_url,
                    defaults={
                        'summary': issue_title, # Use title as summary
                        'raw_data': issue_raw
                    }
                )
                # Add the issue to this specific RepositoryWork entry
                repo_work.issues.add(issue_obj)

            # --- Process Commits ---
            commits_data = work_info.get('commits', [])
            for commit_info in commits_data:
                commit_url = commit_info.get('url')
                if not commit_url: continue

                # Prepare raw_data for Commit (exclude url and sha)
                commit_raw = {k: v for k, v in commit_info.items() if k not in ['url', 'sha']}
                commit_summary = commit_info.get('message', 'No Message') # Use message as summary

                commit_obj, commit_created = Commit.objects.get_or_create(
                    url=commit_url,
                    defaults={
                        'summary': commit_summary,
                        'raw_data': commit_raw
                    }
                )
                # Add the commit to this specific RepositoryWork entry
                repo_work.commits.add(commit_obj)

            # --- Link RepositoryWork to Contributor ---
            contributor.works.add(repo_work)
            # print(f"        Linked RepositoryWork for {repo_name} to {username}") # Verbose logging

        processed_count += 1
        print(f"  Processed {username}. ({processed_count}/{len(contributors_data)})")

    print("\nDatabase population complete.")


if __name__ == "__main__":
    print("Starting database population script...")
    populate_database(JSON_FILE_PATH)
    print("Script finished.")