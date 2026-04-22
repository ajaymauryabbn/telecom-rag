# Deploying Telecom RAG to Hugging Face Spaces

This guide explains how to deploy the Telecom RAG application to Hugging Face Spaces. Hugging Face Spaces offers a generous free tier for hosting Docker containers with no hard cold-start penalties for the first 48 hours of inactivity.

## Option 1: Automatic Deployment via GitHub Actions (Recommended)

We have configured a GitHub Actions workflow (`.github/workflows/huggingface.yml`) that will automatically sync your `main` branch to Hugging Face Spaces whenever you push to GitHub.

### Step 1: Create a Hugging Face Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. **Space name**: e.g., `telecom-rag`
3. **License**: Choose your preferred license (e.g., `mit` or `apache-2.0`).
4. **Select the Space SDK**: Choose **Docker** -> **Blank**.
5. **Space hardware**: Choose **Free** (CPU basic - 16GB, 2vCPU).
6. Click **Create Space**.

### Step 2: Get your Hugging Face Token
1. Go to your Hugging Face [Access Tokens](https://huggingface.co/settings/tokens) page.
2. Click **New token**.
3. Name it (e.g., `github-actions`), select **Write** role, and create it.
4. Copy the token.

### Step 3: Add Secrets to GitHub
1. Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret** and add the following three secrets:
   - `HF_TOKEN`: The token you created in Step 2.
   - `HF_USERNAME`: Your Hugging Face username (e.g., `ajaymauryabbn`).
   - `HF_SPACE_NAME`: The name of the Space you created in Step 1 (e.g., `telecom-rag`).

### Step 4: Configure Space Secrets on Hugging Face
1. Go to your Hugging Face Space.
2. Click on the **Settings** tab.
3. Scroll down to **Variables and secrets**.
4. Add the following **Secrets**:
   - `OPENAI_API_KEY`: Your OpenAI API key.
   - `GOOGLE_API_KEY` (optional): If using Gemini fallback.
5. (Optional) Add the following **Variables** if you want to override the defaults:
   - `LLM_PROVIDER`: `openai` (default)
   - `EMBEDDING_PROVIDER`: `openai` (default)

### Step 5: Trigger the Deployment
Push your code to the `main` branch on GitHub:
```bash
git add .
git commit -m "Deploy to Hugging Face Spaces"
git push origin main
```
The GitHub Action will automatically run and push the code to your Space. The Space will then build the Docker image and start the application.

---

## Option 2: Direct Deployment (Manual)

If you prefer not to use GitHub Actions, you can push directly to Hugging Face using Git.

1. Create a Space on Hugging Face as described in Option 1 (Step 1).
2. Clone your Hugging Face Space repository:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   ```
3. Copy all the files from this `telecom-rag` repository into the cloned Hugging Face repository.
4. Add, commit, and push the files:
   ```bash
   git add .
   git commit -m "Initial commit for HF Space"
   git push
   ```
5. Configure the Space Secrets (`OPENAI_API_KEY`, etc.) in the Hugging Face Space Settings as described in Option 1 (Step 4).

## Accessing Your App

Once the Space says "Running", you can access the application directly from the Hugging Face Space URL. Because we set `app_port: 7860` in the `README.md` metadata and exposed `7860` in the `Dockerfile`, Hugging Face will automatically route traffic to the Streamlit app.
