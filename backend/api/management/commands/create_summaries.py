import os
import json
import time
import concurrent.futures
from typing import Tuple, Optional, Union, List

import openai # Still use the openai library
from dotenv import load_dotenv

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.db import connection # To close connections in threads

# Assuming your models are in an app named 'api'
# Adjust the import if your app name is different
from api.models import Issue, Commit, RepositoryWork, Contributor # Add Contributor

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# --- Llama Settings ---
LLAMA_MODEL = "Llama-4-Maverick-17B-128E-Instruct-FP8"
LLAMA_BASE_URL = "https://api.llama.com/compat/v1/"

# --- General Settings ---
ISSUES_SYSTEM_PROMPT = """You are an AI assistant specialized in summarizing GitHub issues.
Analyze the provided JSON data representing a GitHub issue.
Generate a concise, informative summary (typically 1-2 sentences, max 3) focusing on the core problem, request, or topic described in the issue title and body (if available in the data).
Ignore metadata like assignees, labels, or timestamps unless they are crucial to the core issue itself.
Extract the essence of the issue based primarily on the 'title' and potentially 'body' fields within the JSON.
If the provided data lacks sufficient information (e.g., missing title/body), output only the text "Cannot summarize".
The summary should be plain text. Do not include markdown formatting like ```json.
"""

COMMITS_SYSTEM_PROMPT = """You are an AI assistant specialized in summarizing GitHub commits.
Analyze the provided JSON data representing a GitHub commit.
Generate a concise, informative summary (typically 1 sentence, max 2) focusing on the *main change* described in the commit message.
If available, briefly mention the types of files changed (e.g., "Updated Python files and documentation") from the 'files_changed' field if it adds significant context, but prioritize the commit message content. Ignore the 'diff_patch' unless the message is uninformative.
If the provided data lacks a meaningful message, output only the text "Cannot summarize".
The summary should be plain text. Do not include markdown formatting like ```json.
"""

REPO_WORK_SYSTEM_PROMPT = """You are an AI assistant summarizing a contributor's work within a specific GitHub repository based on individual issue and commit summaries.
You will be given a list of summaries for closed issues assigned to the contributor and commits authored by them in this repository.
Synthesize these points into a coherent paragraph (2-4 sentences) describing the overall nature and key areas of the contributor's work in *this specific repository*.
Focus on the substance of the contributions (e.g., "Fixed bugs related to X", "Implemented feature Y", "Refactored Z module", "Improved documentation for A and B").
Do not simply list the summaries. Group similar activities if possible.
If the provided list of summaries is empty or uninformative, output only the text "Cannot summarize".
The summary should be plain text.
"""

# --- NEW: Contributor System Prompt ---
CONTRIBUTOR_SYSTEM_PROMPT = """You are an AI assistant creating a profile summary for a GitHub contributor based on summaries of their work across different repositories.
You will be given a list of summaries describing the contributor's work in various repositories.
Synthesize these points into a coherent paragraph (3-5 sentences) describing the contributor's overall activities, common themes in their work, and implied technical skills or areas of expertise.
Focus on identifying patterns: What kind of tasks does this person typically handle (e.g., backend development, frontend fixes, testing, documentation, API design)? What technologies or areas do they seem proficient in?
Avoid just listing the repository summaries. Generalize and infer skills where appropriate.
Example output: "This contributor primarily focuses on backend development, frequently fixing bugs in API endpoints and refactoring database interaction modules across several projects. They demonstrate skills in Python and database management, with some contributions to CI/CD pipeline configurations."
If the provided list of summaries is empty or uninformative, output only the text "Cannot summarize".
The summary should be plain text.
"""


MAX_WORKERS = 5
# Slightly longer timeout for potentially complex synthesis
API_TIMEOUT = 120
REPO_WORK_MAX_TOKENS = 250
# Allow more tokens for the final contributor summary
CONTRIBUTOR_MAX_TOKENS = 350


# --- Function for Processing Issues (Condensed - No Logic Change) ---
def process_single_issue(issue_id: int, api_key: str, base_url: str, model_name: str, system_prompt: str) -> Tuple[int, Optional[str], Optional[str]]:
    summary=None; error_msg=None; client=None; issue=None
    try:
        client=openai.OpenAI(api_key=api_key, base_url=base_url, timeout=API_TIMEOUT)
        issue=Issue.objects.get(pk=issue_id)
        if not isinstance(issue.raw_data, dict) or not issue.raw_data: return issue_id,None,"raw_data invalid."
        raw_data_str=json.dumps(issue.raw_data); user_prompt=f"GitHub issue JSON:\n{raw_data_str}\n\nGenerate summary."
        response=client.chat.completions.create(model=model_name, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],temperature=0.3,max_tokens=100,n=1)
        if response.choices: generated_text=response.choices[0].message.content.strip(); summary=generated_text if generated_text and "cannot summarize" not in generated_text.lower() else None; error_msg="LLM cannot summarize." if not summary and generated_text else None
        else: error_msg="No API choices."
    except Issue.DoesNotExist: error_msg="Issue not found."
    except (openai.RateLimitError,openai.APITimeoutError,openai.APIError) as api_err: error_msg=f"API Error: {type(api_err).__name__}"
    except Exception as e: error_msg=f"Error: {e}"
    finally: connection.close()
    return issue_id, summary, error_msg

# --- Function for Processing Commits (Condensed - No Logic Change) ---
def process_single_commit(commit_id: int, api_key: str, base_url: str, model_name: str, system_prompt: str) -> Tuple[int, Optional[str], Optional[str]]:
    summary=None; error_msg=None; client=None; commit=None
    try:
        client=openai.OpenAI(api_key=api_key, base_url=base_url, timeout=API_TIMEOUT)
        commit=Commit.objects.get(pk=commit_id)
        if not isinstance(commit.raw_data, dict) or not commit.raw_data: return commit_id,None,"raw_data invalid."
        raw_data_str=json.dumps(commit.raw_data); user_prompt=f"GitHub commit JSON:\n{raw_data_str}\n\nGenerate summary."
        response=client.chat.completions.create(model=model_name, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],temperature=0.3,max_tokens=100,n=1)
        if response.choices: generated_text=response.choices[0].message.content.strip(); summary=generated_text if generated_text and "cannot summarize" not in generated_text.lower() else None; error_msg="LLM cannot summarize." if not summary and generated_text else None
        else: error_msg="No API choices."
    except Commit.DoesNotExist: error_msg="Commit not found."
    except (openai.RateLimitError,openai.APITimeoutError,openai.APIError) as api_err: error_msg=f"API Error: {type(api_err).__name__}"
    except Exception as e: error_msg=f"Error: {e}"
    finally: connection.close()
    return commit_id, summary, error_msg


# --- Function for Processing RepositoryWork (Condensed - No Logic Change) ---
def process_single_repo_work(repo_work_id: int, api_key: str, base_url: str, model_name: str, system_prompt: str) -> Tuple[int, Optional[str], Optional[str]]:
    summary=None; error_msg=None; client=None; repo_work=None
    try:
        client=openai.OpenAI(api_key=api_key, base_url=base_url, timeout=API_TIMEOUT)
        repo_work=RepositoryWork.objects.prefetch_related('issues','commits').get(pk=repo_work_id)
        issue_summaries=[iss.summary for iss in repo_work.issues.all() if iss.summary]
        commit_summaries=[com.summary for com in repo_work.commits.all() if com.summary]
        if not issue_summaries and not commit_summaries: return repo_work_id,None,"No item summaries found."
        input_parts=["Contributor activity summaries:"]
        if issue_summaries: input_parts.append("\nIssues:"); input_parts.extend([f"- {s}" for s in issue_summaries])
        if commit_summaries: input_parts.append("\nCommits:"); input_parts.extend([f"- {s}" for s in commit_summaries])
        user_prompt="\n".join(input_parts)+"\n\nGenerate overall work summary."
        response=client.chat.completions.create(model=model_name, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],temperature=0.4,max_tokens=REPO_WORK_MAX_TOKENS,n=1)
        if response.choices: generated_text=response.choices[0].message.content.strip(); summary=generated_text if generated_text and "cannot summarize" not in generated_text.lower() else None; error_msg="LLM cannot summarize." if not summary and generated_text else None
        else: error_msg="No API choices."
    except RepositoryWork.DoesNotExist: error_msg="RepoWork not found."
    except (openai.RateLimitError,openai.APITimeoutError,openai.APIError) as api_err: error_msg=f"API Error: {type(api_err).__name__}"
    except Exception as e: error_msg=f"Error: {e}"
    finally: connection.close()
    return repo_work_id, summary, error_msg


# --- NEW: Function for Processing Contributor ---
def process_single_contributor(
    contributor_id: int, # Use contributor_id
    api_key: str,
    base_url: str,
    model_name: str,
    system_prompt: str # Use the specific contributor prompt
) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Fetches related RepositoryWork summaries, calls API for Contributor summary.
    Designed to be run in a separate thread.
    """
    summary = None
    error_msg = None
    contributor = None
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=API_TIMEOUT)
        try:
            # Fetch Contributor and related RepositoryWork summaries *within the thread*
            contributor = Contributor.objects.prefetch_related('works', 'works__repository').get(pk=contributor_id)
        except Contributor.DoesNotExist: return contributor_id, None, "Contributor object not found."
        except Exception as db_err: return contributor_id, None, f"DB error fetching contributor: {db_err}"

        # --- Collect existing RepoWork summaries ---
        work_summaries_by_repo = {}
        valid_summaries_found = False
        for work in contributor.works.all():
            if work.summary: # Check if the RepositoryWork itself has a summary
                repo_name = work.repository.name if work.repository else "Unknown Repo"
                if repo_name not in work_summaries_by_repo:
                    work_summaries_by_repo[repo_name] = []
                work_summaries_by_repo[repo_name].append(work.summary)
                valid_summaries_found = True

        if not valid_summaries_found:
            return contributor_id, None, "No valid RepositoryWork summaries found to synthesize."

        # --- Format input for the prompt ---
        input_text_parts = ["Summaries of contributor's work across repositories:\n"]
        for repo_name, summaries in work_summaries_by_repo.items():
            input_text_parts.append(f"\nRepository: {repo_name}")
            for s in summaries: # Should typically be one summary per repo_work, but loop just in case
                input_text_parts.append(f"- {s}")

        user_prompt = "\n".join(input_text_parts)
        # Consider truncating user_prompt if it gets extremely long to avoid input token limits
        # MAX_INPUT_LENGTH = 3500 # Example
        # if len(user_prompt) > MAX_INPUT_LENGTH:
        #    user_prompt = user_prompt[:MAX_INPUT_LENGTH] + "\n\n[Input truncated due to length]"

        user_prompt += "\n\nPlease generate an overall profile summary of the contributor's activities and skills based on these points."

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[ {"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}, ],
                temperature=0.5, # Slightly higher temp for more inferential summary
                max_tokens=CONTRIBUTOR_MAX_TOKENS, # Use specific max tokens
                n=1,
            )
            if response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content.strip()
                if generated_text and generated_text.lower() != "cannot summarize":
                    summary = generated_text
                elif generated_text.lower() == "cannot summarize":
                    error_msg = "LLM indicated data was insufficient to summarize."
                else:
                    error_msg = "API returned an empty summary."
            else:
                error_msg = "Failed to get a valid choice from API response."

        except openai.RateLimitError: error_msg = "API rate limit hit (Llama endpoint)."
        except openai.APITimeoutError: error_msg = f"API request timed out after {API_TIMEOUT}s (Llama endpoint)."
        except openai.APIError as e: error_msg = f"API error (Llama endpoint): {e}"
        except Exception as e: error_msg = f"Unexpected error during API call: {e}"

    except Exception as outer_e: error_msg = f"Error processing contributor {contributor_id}: {outer_e}"
    finally: connection.close()
    return contributor_id, summary, error_msg


# --- Updated Command Class ---
class Command(BaseCommand):
    help = f'Generates summaries for Issues, Commits, RepositoryWorks, AND Contributors using Llama ({LLAMA_MODEL}) in parallel.'

    # Generic processing function to reduce repetition in handle()
    def _run_phase(self, phase_name, model_cls, process_func, system_prompt, api_key, base_url, model_name):
        self.stdout.write("\n" + "="*10 + f" Phase {self.phase_num}: Processing {phase_name} " + "="*(29-len(phase_name)))
        self.phase_num += 1

        qs = model_cls.objects.filter(Q(summary__isnull=True) | Q(summary=''))
        item_ids = list(qs.values_list('id', flat=True))
        total_items = len(item_ids)
        phase_success = 0
        phase_errors = 0
        phase_start = time.time()

        if total_items == 0:
            self.stdout.write(self.style.SUCCESS(f"No {phase_name} items found needing summaries."))
            return phase_success, phase_errors # Return counts

        self.stdout.write(f"Found {total_items} {phase_name} items to process.")
        futures = []
        # Use a specific thread name prefix for clarity
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix=f'{phase_name}Worker') as executor:
            for item_id in item_ids:
                futures.append(executor.submit(process_func, item_id, api_key, base_url, model_name, system_prompt))

            # Simplified progress reporting
            processed_count = 0
            for future in concurrent.futures.as_completed(futures):
                processed_count +=1
                try:
                    res_id, summary, error_msg = future.result()
                    if summary:
                        try:
                            # Use filter().update() for efficiency
                            model_cls.objects.filter(pk=res_id).update(summary=summary)
                            phase_success += 1
                        except Exception as db_err:
                            self.stdout.write(self.style.ERROR(f" DB Save Error {phase_name} {res_id}: {db_err}"))
                            phase_errors += 1
                    else:
                        self.stdout.write(self.style.WARNING(f" Failed {phase_name} {res_id}: {error_msg}"))
                        phase_errors += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f" Future Error {phase_name}: {e}"))
                    phase_errors += 1
                # Log progress periodically
                if processed_count % (max(1, total_items // 10)) == 0 or processed_count == total_items:
                     self.stdout.write(f"  Processed {processed_count}/{total_items} {phase_name}...")


        phase_duration = time.time() - phase_start
        self.stdout.write(self.style.SUCCESS(f"{phase_name} processing finished in {phase_duration:.2f}s. Success: {phase_success}, Failed: {phase_errors}"))
        return phase_success, phase_errors # Return counts


    def handle(self, *args, **options):

        llama_api_key = os.getenv('LLAMA_API_KEY')
        if not llama_api_key:
            raise CommandError("LLAMA_API_KEY environment variable not found.")

        self.stdout.write(self.style.NOTICE(f"Using Llama model: {LLAMA_MODEL}, Base URL: {LLAMA_BASE_URL}"))
        self.stdout.write(self.style.NOTICE(f"Max parallel workers: {MAX_WORKERS}, API Timeout: {API_TIMEOUT}s"))

        total_start_time = time.time()
        overall_success_count = 0
        overall_error_count = 0
        self.phase_num = 1 # Initialize phase counter for reporting

        # Run Phase 1: Issues
        s, e = self._run_phase("Issues", Issue, process_single_issue, ISSUES_SYSTEM_PROMPT, llama_api_key, LLAMA_BASE_URL, LLAMA_MODEL)
        overall_success_count += s; overall_error_count += e

        # Run Phase 2: Commits
        s, e = self._run_phase("Commits", Commit, process_single_commit, COMMITS_SYSTEM_PROMPT, llama_api_key, LLAMA_BASE_URL, LLAMA_MODEL)
        overall_success_count += s; overall_error_count += e

        # Run Phase 3: RepositoryWork
        s, e = self._run_phase("RepoWork", RepositoryWork, process_single_repo_work, REPO_WORK_SYSTEM_PROMPT, llama_api_key, LLAMA_BASE_URL, LLAMA_MODEL)
        overall_success_count += s; overall_error_count += e

        # Run Phase 4: Contributors
        s, e = self._run_phase("Contributors", Contributor, process_single_contributor, CONTRIBUTOR_SYSTEM_PROMPT, llama_api_key, LLAMA_BASE_URL, LLAMA_MODEL)
        overall_success_count += s; overall_error_count += e


        # --- Final Overall Report ---
        total_duration = time.time() - total_start_time
        self.stdout.write("\n" + "="*30)
        self.stdout.write(self.style.SUCCESS(f"All processing finished in {total_duration:.2f} seconds."))
        self.stdout.write(f"Total successful updates (all phases): {overall_success_count}")
        self.stdout.write(f"Total failed/skipped (all phases): {overall_error_count}")
        self.stdout.write("="*30)