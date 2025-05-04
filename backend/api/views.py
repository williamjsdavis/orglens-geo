import os
import time # Optional: for slight delay if needed during testing
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openai import OpenAI, APIError # Make sure to import OpenAI and potential errors
from django.conf import settings
from .models import *
from .serializers import DataSerializer

try:
    client = OpenAI(api_key=settings.LLAMA_API_KEY, 
            base_url="https://api.llama.com/compat/v1/")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None # Set client to None if initialization fails


# --- Simple Test View ---
@api_view(['GET'])
def get_data(request):
    """
    A simple endpoint to return the data.
    """
    data = DataSerializer()
    data = data.to_representation(data)
    return Response(data)


# --- LLM Streaming View ---

def generate_openai_stream(system_prompt, user_prompt):
    """
    Generator function to stream responses from OpenAI API.
    Yields chunks of text content.
    """
    if not client:
        yield "Error: OpenAI client not initialized. Check API key."
        return
    if not system_prompt or not user_prompt:
        yield "Error: No prompt provided."
        return

    try:
        stream = client.chat.completions.create(
            model="Llama-4-Maverick-17B-128E-Instruct-FP8", # Or your preferred model
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content

    except APIError as e:
        print(f"OpenAI API Error: {e}")
        yield f"\n\nError communicating with OpenAI: {e.message}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        yield f"\n\nAn unexpected error occurred: {str(e)}"

def get_system_prompt():
    return """
    You are a helpful assistant that helps engineers, product managers and managers understand a codebase of multiple repositories.
    You will be given a list of repositiories with a description, as well as a list of contributors with their contributions.
    You will be asked to answer questions about the codebase, and you should find which contributor(s) are the most relevant to answer the question.
    Each contributor has a unique id that you will use to refer to them.
    Your answer should be markdown formatted, explain your reasoning and mention the contributor(s) you are referring to.
    When mentionning a contributor, use the format: <contributor id="id">contributor name</contributor>.
    For example: <contributor id="1">John Doe</contributor>. Do not start the tags with `.
    """


def get_user_prompt(user_question):
    """
    Formats repository and contributor data along with the user question
    into a structured prompt for the LLM.
    """
    data = DataSerializer()
    data = data.to_representation(data)
    repositories_data = data.get('repositories', [])
    contributors_data = data.get('contributors', [])

    # Create a lookup for repository names by ID for easy access later
    repo_id_to_name = {repo['id']: repo['name'] for repo in repositories_data}

    prompt_parts = []

    # --- Repositories Section ---
    prompt_parts.append("## Repositories\n")
    if repositories_data:
        for repo in repositories_data:
            prompt_parts.append(f"### Repository: {repo.get('name', 'N/A')} (ID: {repo.get('id', 'N/A')})")
            prompt_parts.append(f"**URL:** {repo.get('url', 'N/A')}")
            prompt_parts.append(f"**Summary:**\n{repo.get('summary', 'No summary provided.')}\n")
    else:
        prompt_parts.append("No repository data available.\n")

    prompt_parts.append("\n----------\n") # Separator

    # --- Contributors Section ---
    prompt_parts.append("## Contributors\n")
    if contributors_data:
        for contributor in contributors_data:
            prompt_parts.append(f"### Contributor: {contributor.get('username', 'N/A')} (ID: {contributor.get('id', 'N/A')})")
            prompt_parts.append(f"**URL:** {contributor.get('url', 'N/A')}")
            prompt_parts.append(f"**Overall Summary:**\n{contributor.get('summary', 'No summary provided.')}\n")

            works = contributor.get('works', [])
            if works:
                prompt_parts.append("**Contributions by Repository:**")
                for work in works:
                    repo_id = work.get('repository')
                    repo_name = repo_id_to_name.get(repo_id, f"Unknown Repo (ID: {repo_id})")
                    prompt_parts.append(f"- **Repository:** {repo_name}")
                    prompt_parts.append(f"  - **Work Summary:** {work.get('summary', 'No summary provided.')}")
                    # Optionally add Issue/Commit summaries if needed and available
                    issues = work.get('issues', [])
                    commits = work.get('commits', [])
                    if issues: 
                        prompt_parts.append("    - Relevant Issues:")
                        for issue in issues: # Limit for brevity
                            prompt_parts.append(f"      - {issue.get('summary', 'N/A')}")
                    if commits:
                        prompt_parts.append("    - Relevant Commits:")
                        for commit in commits: # Limit for brevity
                            prompt_parts.append(f"      - {commit.get('summary', 'N/A')}")
                prompt_parts.append("") # Add a newline after each contributor's works
            else:
                prompt_parts.append("No specific repository contributions listed.\n")
            prompt_parts.append("\n---\n") # Separator between contributors

    else:
        prompt_parts.append("No contributor data available.\n")

    prompt_parts.append("\n----------\n") # Separator

    # --- User Question Section ---
    prompt_parts.append("## User Question\n")
    prompt_parts.append(user_question)

    return "\n".join(prompt_parts)



@api_view(['POST'])
def llm_stream_view(request):
    """
    Handles POST requests containing a 'prompt' and returns a StreamingHttpResponse
    with the OpenAI completion stream.
    """
    user_question = request.data.get('prompt')

    if not user_question:
        return HttpResponseBadRequest("Missing 'prompt' in request body.")

    if not client:
         return JsonResponse({"error": "OpenAI client not configured"}, status=503) # 503 Service Unavailable
    
    system_prompt = get_system_prompt()

    user_prompt = get_user_prompt(user_question)

    print(f"System Prompt: {system_prompt}")
    print(f"User Prompt: {user_prompt}")

    try:
        # Create the generator
        stream_generator = generate_openai_stream(system_prompt, user_prompt)


        response = StreamingHttpResponse(
            stream_generator,
            content_type='text/plain; charset=utf-8' # Simpler for basic fetch handling
        )
        return response

    except Exception as e:
        # Catch potential errors during generator setup (though most are handled inside)
        print(f"Error setting up stream view: {e}")
        return JsonResponse({"error": f"Failed to start stream: {str(e)}"}, status=500)