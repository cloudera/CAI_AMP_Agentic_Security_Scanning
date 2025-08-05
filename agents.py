import yaml
import os
import json
from typing import Callable, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import git
import subprocess
import sys
from openai import OpenAI
import tempfile
import chunks
from datetime import datetime

class AgenticWorkflow:
    """
    Top-level parent class for the Agentic AI Workflow System.
    Contains all components needed for multi-agent AI workflows.
    """
    
    def __init__(self):
        """Initialize the AgenticWorkflow system."""
        self.version = "1.0.0"
        self.description = "Multi-agent AI workflow system"
    
    class LLMClient:
        """Client for managing LLM connections and API calls."""
        
        def __init__(
            self,
            client_type: str = "caii",
            assumed_role: Optional[str] = None,
            endpoint_url: Optional[str] = None,
            region: Optional[str] = None,
            max_tokens: int = 64000,
            jwt: str = "",
            url: Optional[str] = None,
            model_id: str = "",
        ):
            """Initialize the LLM client with optional configuration overrides."""
            self.max_tokens = max_tokens
            self.client_type = client_type
            self.jwt = jwt
            self.model_id = model_id
            
            # Determine which URL to use (prioritize 'url' over 'endpoint_url')
            target_url = url if url is not None else endpoint_url
            self.url = target_url
            
            # Initialize the appropriate client based on type
            if client_type == "bedrock":
                self._init_bedrock_client(assumed_role, target_url, region)
            elif client_type == "caii":
                self._init_caii_client(target_url)
            else:
                raise ValueError(f"Unsupported client_type: {client_type}. Supported types: 'bedrock', 'caii'")

        def _init_bedrock_client(self, assumed_role, url, region):
            """Initialize AWS Bedrock client."""
            if region is None:
                target_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
            else:
                target_region = region

            print(f"Create new Bedrock client\\n  Using region: {target_region}")
            session_kwargs = {"region_name": target_region}
            client_kwargs = {**session_kwargs}

            config = Config(read_timeout=36000)
            profile_name = os.environ.get("AWS_PROFILE")
            if profile_name:
                print(f"  Using profile: {profile_name}")
                session_kwargs["profile_name"] = profile_name

            retry_config = Config(
                region_name=target_region,
                read_timeout=36000,
                retries={
                    "max_attempts": 10,
                    "mode": "standard",
                },
            )
            session = boto3.Session(**session_kwargs)

            if assumed_role:
                print(f"  Using role: {assumed_role}", end='')
                sts = session.client("sts")
                response = sts.assume_role(
                    RoleArn=str(assumed_role),
                    RoleSessionName="langchain-llm-1"
                )
                client_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
                client_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
                client_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]

            if url:
                client_kwargs["endpoint_url"] = url

            self.bedrock_client = session.client(
                service_name="bedrock-runtime",
                config=retry_config,
                **client_kwargs
            )

            print("boto3 Bedrock client successfully created!")
            print(self.bedrock_client._endpoint)
            
        def _init_caii_client(self, url):
            """Initialize Cloudera AI Inference client."""
            try:
                # Get JWT token from parameter or environment
                if self.jwt:
                    # Use provided JWT parameter
                    jwt_data = json.loads(self.jwt)
                    api_key = jwt_data["token"]
                    print("Using provided JWT token")
                else:
                    # Read from CDP_TOKEN environment variable
                    cdp_token = os.environ.get("CDP_TOKEN")
                    if not cdp_token:
                        raise RuntimeError("No JWT provided and CDP_TOKEN environment variable not set. Please provide JWT token or set CDP_TOKEN.")
                    
                    jwt_data = json.loads(cdp_token)
                    api_key = jwt_data["token"]
                    print("Using CDP_TOKEN from environment")
                
                # Initialize OpenAI client with Cloudera AI Inference endpoint
                self.caii_client = OpenAI(
                    base_url=url,
                    api_key=api_key,
                )
                
                print("Cloudera AI Inference client successfully created!")
                print(f"Using endpoint: {url}")
                
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JWT format. Expected valid JSON: {e}")
            except KeyError:
                raise RuntimeError("Invalid JWT structure. Expected 'token' key in JSON.")

        def _call_llm(self, prompt: str, truncate_input: bool = False, use_chunks: bool = True) -> str:
            """Call the LLM with the provided prompt."""
            try:
                # Calculate max input characters based on token limit (4 chars per token estimate), reserve 25% of tokens for output
                max_input_chars = 2 * self.max_tokens 
                
                # If using chunks, process iteratively
                if use_chunks:
                    return self._process_with_chunks(prompt, max_input_chars)
                
                # Handle input truncation if requested
                if truncate_input:
                    if len(prompt) > max_input_chars:
                        truncated_prompt = prompt[:max_input_chars] + "\n\n[INPUT TRUNCATED DUE TO LENGTH - ANALYSIS CONTINUES WITH AVAILABLE CONTENT]"
                        print(f"Warning: Input truncated from {len(prompt)} to {len(truncated_prompt)} characters")
                        prompt = truncated_prompt
                else:
                    # Check if input is too long and raise exception
                    if len(prompt) > max_input_chars:
                        raise ValueError(f"Input too long: {len(prompt)} characters (~{len(prompt)//4} tokens). "
                                       f"Maximum supported: {max_input_chars} characters (~{max_input_chars//4} tokens). "
                                       f"Consider processing smaller sections of the repository or using file filtering.")
                
                return self._single_llm_call(prompt)
                
            except Exception as e:
                print(f"Error calling LLM: {str(e)}")
                return f"Error: {str(e)}"
                raise

        def _process_with_chunks(self, prompt: str, chunk_size: int) -> str:
            """Process the prompt using chunks and concatenate results."""
            temp_files = []
            output_files = []
            
            try:
                # Create temporary file for the prompt
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
                    temp_file.write(prompt)
                    temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)
                
                # Initialize the chunker with the specified size
                chunker = chunks.MarkdownChunker(chunk_size=chunk_size)
                
                # Run the chunker on the file
                markdown_chunks = chunker.chunk_file(temp_file_path)
                
                print(f"\nFound {len(markdown_chunks)} chunks with chunk_size={chunk_size}.\n")
                
                # Process each chunk
                for i, chunk in enumerate(markdown_chunks):
                    print(f"--- Processing Chunk {i+1} (Length: {len(chunk)}) ---")
                    
                    # Call LLM for this chunk
                    chunk_response = self._single_llm_call(chunk)
                    
                    # Save chunk response to temporary file
                    with tempfile.NamedTemporaryFile(mode='w', suffix=f'_chunk_{i+1}.md', delete=False) as output_file:
                        output_file.write(chunk_response)
                        output_files.append(output_file.name)
                    
                    print(f"Completed chunk {i+1}/{len(markdown_chunks)}")
                
                # Concatenate all outputs
                final_response = ""
                for output_file in output_files:
                    with open(output_file, 'r') as f:
                        final_response += f.read() + "\n\n"
                
                return final_response.strip()
                
            except FileNotFoundError as e:
                print(f"Error: {e}")
                print("Please ensure the MarkdownChunker class is defined correctly.")
                raise
            except Exception as e:
                print(f"An unexpected error occurred during chunking: {e}")
                raise
            finally:
                # Clean up temporary files
                for temp_file in temp_files + output_files:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except Exception as e:
                        print(f"Warning: Could not delete temporary file {temp_file}: {e}")

        def _single_llm_call(self, prompt: str) -> str:
            """Make a single LLM call with the provided prompt."""
            # Print timestamp before LLM call
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            print(f"[{timestamp}] Making LLM call with model: {self.model_id}")
            
            if self.client_type == "bedrock":
                return self._single_bedrock_call(prompt)
            elif self.client_type == "caii":
                return self._single_caii_call(prompt)
            else:
                raise ValueError(f"Unsupported client_type: {self.client_type}")

        def _single_bedrock_call(self, prompt: str) -> str:
            """Make a single AWS Bedrock call."""
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens, 
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            try:
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=body,
                    contentType="application/json",
                    accept="application/json"
                )
                # Process successful response
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                print(f"Bedrock invocation failed: {error_code} - {error_message}")
                raise
                # Implement specific error handling logic based on error_code
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        def _single_caii_call(self, prompt: str) -> str:
            """Make a single Cloudera AI Inference call."""
            try:
                response = self.caii_client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.1
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"CAII invocation failed: {e}")
                raise
    
    class Agent:
            """Represents a single agent in the AI system."""
            def __init__(self, agent_config: dict, llm_client: Optional['AgenticWorkflow.LLMClient'] = None, truncate_input: bool = False, use_chunks: bool = True, client_type: str = "caii", jwt: str = "", model_id: str = ""):
                self.name = agent_config.get("name")
                self.description = agent_config.get("description")
                self.objective = agent_config.get("objective")
                self.core_responsibilities = agent_config.get("core_responsibilities", [])
                self.key_traits = agent_config.get("key_traits", [])
                self.input_sample = agent_config.get("input_sample", "")
                self.output_sample = agent_config.get("output_sample", "")
                self.truncate_input = truncate_input
                self.use_chunks = use_chunks
                self.client_type = client_type
                
                # LLM client - create one if not provided
                self.llm_client = llm_client if llm_client else AgenticWorkflow.LLMClient(client_type=self.client_type, jwt=jwt, model_id=model_id)
                
                if not self.name or not self.objective:
                    raise ValueError("Agent configuration must include 'name' and 'objective'.")

            def execute(self, input_content: str, output_path: str) -> str:
                """Executes the agent's task by formatting a prompt and calling the LLM."""
                try:
                    if not isinstance(input_content, str):
                        raise ValueError(f"Input content must be a string, got {type(input_content)}")
                    if not isinstance(output_path, str):
                        raise ValueError(f"Output path must be a string, got {type(output_path)}")
                    
                    prompt = self._format_prompt(input_content, output_path)
                    
                    if not prompt or not isinstance(prompt, str):
                        raise ValueError(f"Generated prompt is invalid: {type(prompt)}")
                    
                    # Validate inputs
                    if not isinstance(prompt, str):
                        raise ValueError(f"Prompt must be a string, got {type(prompt)}")
                    
                    response = self.llm_client._call_llm(prompt, truncate_input=self.truncate_input, use_chunks=self.use_chunks)
                    print(f"Received response (length: {len(response)} chars)")
                    return response
                    
                except Exception as e:
                    error_msg = f"Error executing agent '{self.name}': {str(e)}"
                    return f"Error: {error_msg}"

            def _format_prompt(self, input_content: str, output_path: str) -> str:
                """Creates a detailed, structured prompt for the LLM."""
                responsibilities = "\\n".join(f"- {r}" for r in self.core_responsibilities)
                traits = ", ".join(self.key_traits)
                
                file_extension = os.path.splitext(output_path)[1].lower()
                if file_extension == '.json':
                    output_format_instruction = "Your final output must be a single, valid JSON object and nothing else."
                elif file_extension == '.md':
                    output_format_instruction = "Your final output must be formatted in Markdown."
                else:
                    output_format_instruction = "Your final output should be plain text."

                input_sample_section = ""
                if self.input_sample.strip():
                    input_sample_section = f"""
--- INPUT SAMPLE ---
Here is an example of the type of input you might receive:
{self.input_sample.strip()}
--- END INPUT SAMPLE ---
"""

                output_sample_section = ""
                if self.output_sample.strip():
                    output_sample_section = f"""
--- OUTPUT SAMPLE ---
Here is an example of the expected output format:
{self.output_sample.strip()}
--- END OUTPUT SAMPLE ---
"""

                return f"""
You are an AI agent with the following characteristics:
- Name: {self.name}
- Description: {self.description}
- Key Traits: {traits}

Your primary objective is:
{self.objective}

Your core responsibilities are:
{responsibilities}
{input_sample_section}{output_sample_section}
Based on the input data below, perform your task and generate the required output.
**Output Format Requirement:** {output_format_instruction}

--- INPUT DATA ---
{input_content}
--- END INPUT DATA ---

Generate your response now.
"""


    
    class GitRepoProcessor:
        """Processes git repositories into markdown context files for agent input."""
        
        def __init__(self, repo_url: str, clone_path: Optional[str] = None):
            """Initialize the GitRepoProcessor with repository URL and optional clone path."""
            self.repo_url = repo_url
            self.clone_path = clone_path or os.path.join(os.getcwd(), 'cloned_repo')
            self.cloned_repo = None
            
        def clone_repository(self) -> str:
            """Clone the repository and return the clone path."""
            # Remove existing directory if it exists
            if os.path.exists(self.clone_path):
                import shutil
                shutil.rmtree(self.clone_path)
            
            try:
                # Clone the repository
                self.cloned_repo = git.Repo.clone_from(self.repo_url, self.clone_path)
                return self.clone_path
            except Exception as e:
                raise
        
        def convert_to_markdown(self, output_path: str = "data/inputs/codebase_context.md") -> str:
            """Convert the cloned repository to markdown using git2text.py."""
            if not self.cloned_repo or not os.path.exists(self.clone_path):
                raise ValueError("Repository must be cloned before conversion. Call clone_repository() first.")
            
            try:               
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Check if git2text.py exists
                git2text_path = "git2text.py"
                if not os.path.exists(git2text_path):
                    raise FileNotFoundError(f"git2text.py not found in current directory. This file is required for markdown conversion.")
                
                # Check if clone path exists and has content
                if not os.path.exists(self.clone_path):
                    raise RuntimeError(f"Clone path does not exist: {self.clone_path}")
                
                clone_contents = os.listdir(self.clone_path)
                if not clone_contents:
                    raise RuntimeError(f"Clone path is empty: {self.clone_path}")
                
                # Get absolute path for output
                abs_output_path = os.path.abspath(output_path)
                
                # Run git2text.py on the cloned repository with output file
                cmd = [sys.executable, git2text_path, self.clone_path, "-o", abs_output_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_details = f"Return code: {result.returncode}"
                    if result.stderr:
                        error_details += f", stderr: {result.stderr}"
                    if result.stdout:
                        error_details += f", stdout: {result.stdout}"
                    raise RuntimeError(f"git2text.py failed - {error_details}")
                
                # Check if output file was created
                if not os.path.exists(abs_output_path):
                    raise RuntimeError(f"git2text.py completed but output file was not created: {abs_output_path}")
                
                return abs_output_path
                
            except Exception as e:
                raise
        
        def process_repository(self, output_path: str = "data/inputs/codebase_context.md") -> str:
            """Complete process: clone repository and convert to markdown context."""
            # Clone the repository
            self.clone_repository()
            
            # Convert to markdown context
            result_path = self.convert_to_markdown(output_path)
            return result_path
        
        def cleanup(self):
            """Clean up cloned repository directory."""
            if os.path.exists(self.clone_path):
                import shutil
                shutil.rmtree(self.clone_path)

    class DAGConstructor:
        """Constructs an executable DAG function from a YAML configuration file."""
        
        def __init__(self, config_path: str = "./sec_agents.yaml", llm_client: Optional['AgenticWorkflow.LLMClient'] = None, truncate_input: bool = False, use_chunks: bool = True, client_type: str = "caii",jwt: str =""):
            """Initialize the constructor by loading and parsing the YAML configuration."""
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.steps = config.get("dag_flow", [])
            self.llm_client = llm_client
            self.truncate_input = truncate_input
            self.use_chunks = use_chunks
            self.client_type = client_type
            self.jwt = jwt
            
            # Create agents with LLM client
            self.agents = {
                agent_def["name"]: AgenticWorkflow.Agent(
                    agent_def, 
                    llm_client=self.llm_client,
                    truncate_input=self.truncate_input,
                    use_chunks=self.use_chunks,
                    client_type=self.client_type,
                    jwt=self.jwt
                ) 
                for agent_def in config.get("agents", [])
            }
            
            if not self.steps or not self.agents:
                raise ValueError("YAML must contain 'dag_flow' and 'agents' definitions.")

        def build_executor(self) -> Callable[[], None]:
            """Build and return a function that executes the entire DAG."""
            def dag_executor():
                """Execute the agentic workflow."""
                try:
                    for i, step_config in enumerate(self.steps):
                        agent_name = step_config["agent"]
                        input_path = step_config["input"]
                        output_path = step_config["output"]

                        print(f"\n ========== Executing Step {i+1}/{len(self.steps)}: {agent_name} ==========")
                        
                        agent = self.agents.get(agent_name)
                        if not agent:
                            raise RuntimeError(f"Agent '{agent_name}' defined in DAG flow but not found in agent definitions.")

                        # Read input file
                        try:
                            with open(input_path, 'r') as f:
                                input_content = f.read()
                        except FileNotFoundError as e:
                            raise RuntimeError(f"Input file not found for step {i+1} ({agent_name}): {input_path}") from e
                        
                        # Execute agent
                        output_content = agent.execute(input_content, output_path)
                        
                        # Check if agent execution returned an error
                        if output_content.startswith("Error:"):
                            raise RuntimeError(f"Step {i+1} ({agent_name}) failed: {output_content}")

                        # Write output file
                        try:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, 'w') as f:
                                f.write(output_content)
                        except Exception as e:
                            raise RuntimeError(f"Failed to write output file for step {i+1} ({agent_name}): {output_path}") from e
                    
                    print("\\nWorkflow completed successfully.")
                    
                except Exception as e:
                    print(f"\\nWorkflow failed: {str(e)}")
                    raise
            
            return dag_executor
    