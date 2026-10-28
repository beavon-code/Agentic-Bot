# Agentic-Bot

An agentic AI chatbot built with **Streamlit, LangChain, and LangGraph**. The application enables users to interact with an AI model, execute tools, retrieve information from documents, and manage agent workflows.

The project includes a CI/CD pipeline using **GitHub Actions, a self-hosted runner, Docker Hub, and AWS ECS Fargate** to automate container builds and deployments.

## Features

- **Conversational AI:** Interact with an AI model through a Streamlit interface.
- **Agentic workflows:** Coordinate model responses and tool execution using LangChain and LangGraph.
- **Tool integration:** Support tools such as a calculator and stock quote lookup.
- **Retrieval-Augmented Generation (RAG):** Retrieve relevant information from documents using FAISS.
- **Human-in-the-loop:** Pause selected agent actions for human review or approval.
- **Conversation persistence:** Use SQLite checkpointing to preserve conversation state.
- **AI integrations:** Connect to DeepSeek and Groq models.
- **Web search:** Integrate Tavily for external information retrieval.
- **Observability:** Use LangSmith for tracing and monitoring agent execution.
- **Containerization:** Package the application with Docker.
- **Automated deployment:** Push images to Docker Hub and deploy to AWS ECS Fargate.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| LLM orchestration | LangChain |
| Agent workflows | LangGraph |
| AI providers | DeepSeek, Groq |
| Web search | Tavily |
| Vector store | FAISS |
| Conversation persistence | SQLite |
| Monitoring and tracing | LangSmith |
| Containerization | Docker |
| Container registry | Docker Hub |
| CI/CD | GitHub Actions |
| CI/CD runner | Self-hosted GitHub Actions runner |
| Cloud deployment | AWS ECS Fargate |
| Secret management | AWS Secrets Manager |

## Architecture

The deployment workflow follows these steps:

1. A developer pushes code to GitHub.
2. GitHub Actions triggers the CI/CD workflow.
3. A self-hosted runner builds the Docker image.
4. The image is tagged and pushed to Docker Hub.
5. Application secrets are updated in AWS Secrets Manager.
6. A new ECS task definition is registered.
7. ECS Fargate deploys the updated container.
8. The deployment workflow waits for the ECS service to become stable.

## Project Structure

The following is an example structure. Adjust the filenames to match your implementation.

```text
agentic-chatbot/
├── .github/
│   └── workflows/
│       └── cicd.yaml
├── .aws/
│   └── task-definition.json
├── app.py
├── agentic_chatbot_tool_backend.py
├── app_tools_hitl.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
├── protective.pdf
└── chatbot.db
```

Do not commit API keys, credentials, private documents, or database files containing sensitive information.

## Prerequisites

Before running the application, install or configure:

- Python 3.10 or another version compatible with your dependencies.
- Git.
- Docker Desktop or Docker Engine.
- API keys for the AI provider and search service.
- A LangSmith API key if tracing is enabled.
- A Docker Hub account and repository.
- An AWS account with an ECS Fargate cluster and service.
- A registered self-hosted GitHub Actions runner for deployment.

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/beavon-code/Agentic-Bot.git
cd Agentic-Bot
```

Replace the URL with your actual GitHub repository URL.

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Configure the following variables in your local environment or a `.env` file if your application supports loading one.

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=agentic-chatbot
```

Only configure the variables your application actually uses. Never commit real API keys or your `.env` file to GitHub.

### 5. Run the application

If your Streamlit entry point is `app.py`, execute:

```bash
streamlit run app.py
```

Open the address displayed in your terminal, usually:

http://localhost:8501

## Running with Docker

### 1. Build the image

```bash
docker build -t agentic-chatbot:local .
```

### 2. Run the container

```bash
docker run --rm -p 8501:8501 --env-file .env agentic-chatbot:local
```

Open http://localhost:8501 in your browser.

Ensure the Dockerfile starts Streamlit with `--server.address=0.0.0.0` and uses port `8501`.

## CI/CD Pipeline

The project uses GitHub Actions and a self-hosted runner to automate image building and deployment.

### Pipeline stages

1. **Trigger:** A push to the configured branch starts the workflow.
2. **Environment preparation:** The runner checks the required tools and dependencies.
3. **Build:** Docker builds the Streamlit application image.
4. **Registry:** The image is pushed to Docker Hub with a commit-specific tag and a `latest` tag.
5. **Configuration:** Application secrets are stored in AWS Secrets Manager.
6. **Deployment:** The workflow registers a new ECS task definition and updates the ECS service.
7. **Verification:** The workflow waits for the ECS service to become stable.

### Required GitHub Actions secrets

Configure these under **GitHub Repository → Settings → Secrets and variables → Actions**.

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `AWS_DEPLOY_ROLE_ARN` | AWS IAM role assumed through OIDC |
| `AWS_APP_ENV_SECRET_ARN` | ARN of the application secret in AWS Secrets Manager |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `GROQ_API_KEY` | Groq API key |
| `TAVILY_API_KEY` | Tavily API key |
| `LANGSMITH_TRACING` | Enables or disables tracing |
| `LANGSMITH_ENDPOINT` | LangSmith endpoint |
| `LANGSMITH_API_KEY` | LangSmith API key |
| `LANGSMITH_PROJECT` | LangSmith project name |

Configure the workflow's AWS region, ECS cluster name, ECS service name, Docker Hub image name, and container name to match your infrastructure.

### AWS requirements

The deployment requires:

- An existing ECS cluster and Fargate service.
- An ECS task definition configured for the application.
- An ECS task execution role with permission to retrieve the application secrets.
- An IAM deployment role trusted by GitHub Actions through OpenID Connect (OIDC).
- Permissions to update Secrets Manager, register task definitions, and update the ECS service.
- Appropriate network access to external APIs.
- Correct container port and security group configuration.

Use least-privilege IAM permissions and never bake secrets into the Docker image.

## Security Considerations

- Never commit API keys, AWS credentials, access tokens, or `.env` files.
- Use GitHub Actions secrets for CI/CD credentials.
- Use AWS Secrets Manager for application secrets.
- Restrict the GitHub OIDC trust policy to the intended repository and branch or environment.
- Avoid exposing Streamlit directly to the public internet without appropriate security controls.
- Do not commit confidential business documents to a public repository.
- Run the container with only the permissions it needs.

## Troubleshooting

| Problem | Possible solution |
|---|---|
| Streamlit page does not load | Check the entry-point filename, port `8501`, and server address `0.0.0.0`. |
| API authentication fails | Verify that the required API key is valid and configured. |
| Docker build fails | Check the Dockerfile, dependency versions, and `requirements.txt`. |
| GitHub workflow does not start | Check the workflow location, trigger branch, and repository Actions settings. |
| Docker Hub push fails | Verify the username, access token, and repository name. |
| ECS deployment fails | Review ECS service events, task logs, IAM permissions, and networking. |
| Secrets cannot be retrieved | Check the secret ARN, IAM permissions, and JSON key names. |
| Document retrieval fails | Verify the document path and FAISS vector-store configuration. |

## Future Improvements

- Add automated unit and integration tests.
- Add API and tool-execution tests.
- Add Docker image vulnerability scanning.
- Implement deployment smoke tests and health checks.
- Improve structured logging and error handling.
- Add authentication and authorization where required.
- Implement automated rollback procedures.
- Manage AWS infrastructure using infrastructure as code.

## License

Add an appropriate open-source license before distributing this project publicly. Without a license, others generally do not have explicit permission to reuse your code.

---

**Project:** Agentic AI Chatbot  
**Interface:** Streamlit  
**AI Frameworks:** LangChain and LangGraph  
**Container Registry:** Docker Hub  
**Deployment Platform:** AWS ECS Fargate  
**CI/CD:** GitHub Actions with a self-hosted runner
