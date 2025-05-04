import json
import os
from urllib.parse import urlparse
from typing import Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

# Assuming your models are in an app named 'api'
# Adjust the import if your app name is different
from api.models import Repository, Contributor, RepositoryWork, Issue, Commit

# --- Helper Function (copied from fetch.py or imported) ---
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

# --- Django Management Command ---
class Command(BaseCommand):
    help = 'Populates the database with contributor and repository data from a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to the JSON file containing the contributor data.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data in the related tables before populating.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_file_path = options['json_file']
        clear_data = options['clear']

        if not os.path.exists(json_file_path):
            raise CommandError(f"JSON file not found at: {json_file_path}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Error decoding JSON file: {e}")
        except IOError as e:
            raise CommandError(f"Error reading JSON file: {e}")

        if 'contributors' not in data or not isinstance(data['contributors'], list):
            raise CommandError("Invalid JSON format: Expected a 'contributors' key with a list value.")

        contributors_data = data['contributors']

        if clear_data:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            # Clear in reverse order of dependencies
            Commit.objects.all().delete()
            Issue.objects.all().delete()
            RepositoryWork.objects.all().delete()
            Contributor.objects.all().delete()
            Repository.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        self.stdout.write(f"Starting population from {json_file_path}...")

        repo_cache = {} # Cache Repository objects to avoid repeated lookups
        contributor_cache = {} # Cache Contributor objects

        total_contributors = len(contributors_data)
        processed_contributors = 0

        for contributor_data in contributors_data:
            username = contributor_data.get('username')
            if not username:
                self.stdout.write(self.style.WARNING("Skipping contributor entry with missing username."))
                continue

            # --- 1. Create or Update Contributor ---
            contributor, created = Contributor.objects.update_or_create(
                username=username,
                defaults={
                    'url': contributor_data.get('url', ''),
                    'avatar_url': contributor_data.get('avatar_url', ''),
                    'summary': contributor_data.get('summary', ''), # Use summary if available in JSON, else empty
                    # Timestamps are handled automatically
                }
            )
            contributor_cache[username] = contributor
            processed_contributors += 1
            action = "Created" if created else "Updated"
            self.stdout.write(f"[{processed_contributors}/{total_contributors}] {action} contributor: {username}")

            # --- 2. Process Works (Repositories) for this Contributor ---
            works_data = contributor_data.get('works', [])
            for work_data in works_data:
                repo_url = work_data.get('repository_url')
                if not repo_url:
                    self.stdout.write(self.style.WARNING(f"Skipping work entry for contributor {username} due to missing repository_url."))
                    continue

                # --- 3. Create or Update Repository ---
                repository_obj = repo_cache.get(repo_url)
                if not repository_obj:
                    parsed_repo = parse_github_url(repo_url)
                    if not parsed_repo:
                        self.stdout.write(self.style.WARNING(f"Skipping repository {repo_url} for contributor {username} due to invalid URL format."))
                        continue
                    owner, repo_name = parsed_repo
                    full_name = f"{owner}/{repo_name}"

                    # NOTE: The input JSON from fetch.py *doesn't* contain repo summary or avatar_url.
                    # We populate what we can. You might need another step to enrich repo data.
                    repository_obj, repo_created = Repository.objects.update_or_create(
                        url=repo_url,
                        defaults={
                            'name': full_name,
                            'avatar_url': '', # Not available in input JSON
                            'summary': '',     # Not available in input JSON
                            'raw_data': '',    # Could store full repo details if fetched separately
                        }
                    )
                    repo_cache[repo_url] = repository_obj
                    repo_action = "Created" if repo_created else "Updated"
                    if repo_created: # Only log creation to avoid spamming updates
                         self.stdout.write(f"  - {repo_action} repository: {full_name} ({repo_url})")


                # --- 4. Create or Update RepositoryWork ---
                # This links the specific contributor to the specific repository
                repo_work, work_created = RepositoryWork.objects.update_or_create(
                    repository=repository_obj,
                    contributor=contributor,
                    defaults={
                        'summary': f"Work by {username} in {repository_obj.name}", # Example summary
                        # Timestamps are handled automatically
                    }
                )
                work_action = "Created" if work_created else "Found"
                # self.stdout.write(f"    - {work_action} RepositoryWork link for {username} in {repository_obj.name}")


                # --- 5. Create or Update Issues for this RepositoryWork ---
                issues_data = work_data.get('issues', [])
                for issue_data in issues_data:
                    issue_url = issue_data.get('url')
                    if not issue_url:
                        self.stdout.write(self.style.WARNING(f"      - Skipping issue for {username} in {repository_obj.name} due to missing URL."))
                        continue

                    issue_title = issue_data.get('title', 'No Title Provided')
                    # Use url and the specific RepositoryWork link for uniqueness
                    issue, issue_created = Issue.objects.update_or_create(
                        work=repo_work,
                        url=issue_url,
                        defaults={
                            'raw_data': issue_data, # Store the original JSON snippet
                            'summary': issue_title, # Use issue title as summary
                            # Timestamps are handled automatically
                        }
                    )
                    # issue_action = "Created" if issue_created else "Updated"
                    # self.stdout.write(f"      - {issue_action} issue: {issue_url}")


                # --- 6. Create or Update Commits for this RepositoryWork ---
                commits_data = work_data.get('commits', [])
                for commit_data in commits_data:
                    commit_url = commit_data.get('url')
                    # Use commit SHA for primary identification if available, else fallback to URL
                    # Let's use URL as primary key for update_or_create since the model has URL, not SHA
                    if not commit_url:
                        self.stdout.write(self.style.WARNING(f"      - Skipping commit for {username} in {repository_obj.name} due to missing URL."))
                        continue

                    commit_message = commit_data.get('message', 'No commit message.')
                    # Use url and the specific RepositoryWork link for uniqueness
                    commit, commit_created = Commit.objects.update_or_create(
                        work=repo_work,
                        url=commit_url,
                        defaults={
                            'raw_data': commit_data, # Store the original JSON snippet
                            'summary': commit_message, # Use commit message summary as summary
                            # Timestamps are handled automatically
                        }
                    )
                    # commit_action = "Created" if commit_created else "Updated"
                    # self.stdout.write(f"      - {commit_action} commit: {commit_url}")

        self.stdout.write(self.style.SUCCESS("Database population completed successfully!"))