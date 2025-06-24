# Swarm Multi-Agent AI System

This repository contains the backend and frontend for the Swarm Multi-Agent AI System, a platform for real-time, collaborative AI agents.

## Project Structure

- **/backend**: Contains the Flask-SocketIO server, services for AI model integration (OpenRouter), memory (Supermemory), and agent orchestration.
- **/frontend**: Contains the React-based user interface, including all components for chat, agent management, and real-time communication.

## Setup and Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- An active Python virtual environment is recommended.

### 1. Backend Setup
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 2. Frontend Setup
Install and build the frontend application:
```bash
cd frontend
npm install
npm run build
```

## Environment Variables

Create a `.env` file in the project root and add the following variables. Do not commit this file to version control.

```bash
# Flask and Server Settings
FLASK_ENV="development"
SECRET_KEY="your-random-secret-key"

# External Service Keys
OPENROUTER_API_KEY="[your-openrouter-api-key]"
SUPERMEMORY_API_KEY="[your-supermemory-api-key]"
SUPERMEMORY_BASE_URL="https://api.supermemory.ai"
MCP_SERVER_URL="[your-mcp-server-url]"
```

## Running the Application

To run the application, use the single, consolidated server entry point:

```bash
python app.py
```

The application will be available at http://localhost:5000.