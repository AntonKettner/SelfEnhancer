![Self-Enhancing AI Logo](assets/logo.png)

# 🧠 Self-Enhancing AI Codebase (v0.02)

> An experimental framework for exploring AI-driven code optimization

## 🚀 Project Overview

The Self-Enhancing AI Codebase Project (Version 0.02) is an innovative experiment that utilizes artificial intelligence to autonomously improve and extend its own source code. This system uses advanced language models to analyze code, propose improvements, implement, and verify them, creating a self-developing software ecosystem.

## ✨ Key Features

1. 🤖 Autonomous Improvement: The system can independently generate, evaluate, and implement improvement ideas.
2. 👥 Multi-Agent Architecture: Uses separate agents for code generation and control/verification.
3. 🎛️ Interactive User Control: Allows users to approve, test, or reject proposed changes.
4. 🔄 Version Control Integration: Works seamlessly with Git for change management.
5. 💰 Cost Monitoring: Monitors and reports API usage and associated costs.
6. 🔒 Safe Codebase Modification: Works on a copy of the original codebase to prevent unintended changes.

## 🏗️ System Architecture

![System Architecture Diagram](assets/0_01_flowchart_self_enhancer.png)

The project consists of several key components:

- CodeAgent: Responsible for generating improvement ideas, planning implementations, and suggesting code changes.
- ControllingAgent: Evaluates ideas, reviews implementations, and ensures quality control.
- Enhancer: The main orchestrator that manages the improvement cycles and user interactions.

## 🔄 Improvement Process

1. 💡 Idea Generation: The system analyzes the current codebase and suggests potential improvements.
2. ⚖️ Idea Evaluation: Ideas are evaluated based on their potential impact and feasibility.
3. 📝 Implementation Planning: A step-by-step plan is created for each selected idea.
4. 🛠️ Code Modification: The system suggests specific code changes to implement each step.
5. 🔍 Review and Iteration: Proposed changes are reviewed, possibly modified, and iterated until satisfactory.
6. 👍 User Approval: Users can choose to test, directly apply, or reject changes.

## 🚀 Getting Started

1. Clone the repository:   ```
   git clone https://github.com/yourusername/self-enhancing-ai.git
   cd self-enhancing-ai   ```

2. Install the dependencies:   ```
   pip install -r requirements.txt   ```

3. Set up your OpenAI API key in a `.env` file (see Configuration section below)

4. Run the Enhancer:   ```
   python enhancer.py   ```

## ⚙️ Configuration

The project uses environment variables for configuration. Create a `.env` file in the project root with the following content:

### Required Configuration

- `OPENAI_API_KEY`: Your OpenAI API key. Obtain this from the OpenAI website.

### Optional Configuration

- `MODEL_NAME`: The name of the OpenAI model to use. Default is "gpt-3.5-turbo".
- `MAX_TOKENS`: The maximum number of tokens to generate in each API call. Default is 4000.
- `TEMPERATURE`: Controls the randomness of the model's output. Higher values (e.g., 0.8) make the output more random, while lower values (e.g., 0.2) make it more focused and deterministic. Default is 0.7.
- `BASE_DIR`: The base directory for the project. Default is "./" (current directory).
- `GITHUB_TOKEN`: Your GitHub personal access token, if you want to enable GitHub integration.
- `USE_GITHUB`: Set to "true" to enable GitHub integration, "false" to disable it. Default is false.
- `COST_LIMIT`: The maximum cost in USD that you're willing to spend on API calls. The system will stop when this limit is reached. Default is 10.0.

### Customizing the Configuration

You can modify these values to adjust the behavior of the Self-Enhancing AI:

- Increase `MAX_TOKENS` for more detailed responses, but be aware this will increase API usage and costs.
- Adjust `TEMPERATURE` to control the creativity vs. consistency of the AI's suggestions.
- Set `USE_GITHUB` to true and provide a `GITHUB_TOKEN` to enable automatic commits and pull requests for changes.
- Modify `COST_LIMIT` to control your maximum spending on API calls.

Remember to keep your `.env` file secure and never commit it to version control. The `.gitignore` file in this project is set up to exclude the `.env` file by default.

### Advanced Configuration

For advanced users, you can also set the following environment variables:

- `OPENAI_ORG_ID`: Your OpenAI organization ID, if you're using an organization account.
- `RETRY_ATTEMPTS`: Number of retry attempts for API calls in case of failures. Default is 3.
- `RETRY_DELAY`: Delay (in seconds) between retry attempts. Default is 5.

These advanced options allow for more fine-grained control over the API interaction and error handling.
