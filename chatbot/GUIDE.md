# Chatbot Setup and Testing Guide

Follow these step-by-step instructions to run and test the Business Assistant Chatbot project locally on Windows.

## 1. Prerequisites

Ensure you have Python installed on your system. You can check this by running the following command in your PowerShell or Command Prompt:

```powershell
python --version
```

## 2. Set Up a Virtual Environment (Recommended)

It's best practice to use a virtual environment to manage your project dependencies. Open your terminal, navigate to the `chatbot` directory (`cd c:\Users\karti\OneDrive\Desktop\SwifReply\chatbot`), and run:

```powershell
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment on Windows
.\venv\Scripts\activate
```

*(You should see `(venv)` prefix in your terminal prompt after activation.)*

## 3. Install Dependencies

With your virtual environment activated, install all the required Python packages listed in `requirements.txt`:

```powershell
pip install -r requirements.txt
```

## 4. Run the Application

Since you have already pasted your API key into the `.env` file, you are ready to start the backend server. Start the FastAPI application using Uvicorn:

```powershell
uvicorn main:app --reload --port 8000
```

- `--reload` enables auto-reloading so the server restarts whenever you save code changes.
- `--port 8000` tells the server to listen on port 8000.

## 5. Test the Project

### A. Health Check API

To verify that the server is running properly and has successfully loaded the rules, visit the health endpoint in your browser:

👉 **[http://localhost:8000/api/health](http://localhost:8000/api/health)**

You should see a JSON response similar to: `{"status": "ok", "rules_loaded": <number>}`

### B. Interactive Chatbot UI

To use the chatbot interface, simply open the main URL in your web browser:

👉 **[http://localhost:8000](http://localhost:8000)**

This will serve the `index.html` frontend where you can type messages and interact with the Business Assistant!

## Troubleshooting

- **Port in Use:** If port 8000 is already in use, you can run the app on a different port by modifying the command (e.g., `uvicorn main:app --reload --port 8001`).
- **ModuleNotFoundError:** Ensure your virtual environment is activated and you have run the `pip install -r requirements.txt` command.
