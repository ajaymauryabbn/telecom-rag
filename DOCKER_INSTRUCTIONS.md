# Docker Deployment Instructions

## Prerequisites
- Docker Desktop installed (Mac/Windows/Linux)
- Git (optional, if cloning)

## Quick Start (Local Development)

The easiest way to run the Telecom RAG system is using Docker Compose. This will start both the Application and the Redis cache.

1.  **Configure Environment Variables**:
    Ensure you have a `.env` file in the root directory (same level as `docker-compose.yml`). It should contain your API keys:
    ```bash
    OPENAI_API_KEY=sk-...
    HF_TOKEN=hf_...
    # Optional:
    # GOOGLE_API_KEY=...
    # EMBDDING_PROVIDER=openai
    ```

2.  **Build and Run**:
    Run the following command in your terminal:
    ```bash
    docker-compose up --build
    ```

3.  **Access the Application**:
    Open your browser and navigate to: [http://localhost:8501](http://localhost:8501)

4.  **Stop the Application**:
    Press `Ctrl+C` in the terminal, or run:
    ```bash
    docker-compose down
    ```

## Cloud Deployment (Production)

For deploying to cloud platforms (like Google Cloud Run or AWS ECS), you can use the `Dockerfile` directly.

1.  **Build the Image**:
    ```bash
    docker build -t telecom-rag .
    ```

2.  **Run the Container**:
    ```bash
    docker run -p 8501:8501 --env-file .env telecom-rag
    ```
    *Note: Without a Redis instance available, the application will fallback to in-memory caching (non-persistent).*

## Troubleshooting

-   **Redis Connection Error**: Ensure the `redis` service is running. Usage of `docker-compose` handles this automatically.
-   **Missing API Keys**: Check that your `.env` file is populated and passed to the container.
-   **Port Conflicts**: If port 8501 is in use, modify the `ports` section in `docker-compose.yml` (e.g., `"8502:8501"`).
