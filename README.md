# Swarm Multi-Agent System v3.0

> A Unified Multi-Agent Platform for Advanced Orchestration and Production-Ready Infrastructure

[](https://github.com/copp1723/multi_uni_merge)
[](https://www.google.com/search?q=./docs/TEST_RESULTS.md)
[](https://www.google.com/search?q=./docs/)

## **Overview**

This is the v3.0 enhanced system that combines the sophisticated orchestration from `swarm-agents-unified` with the production infrastructure from `swarm-multi-agent-system`. The result is a unified platform with capabilities that exceed those of the original systems.

### **Key Features**

  - **Six Enhanced Agents**: Includes a Communication Agent with authentic tone understanding.
  - **Cross-Agent Memory**: Enabled through Supermemory integration for shared context.
  - **Real-time Chat Interface**: Features WebSocket support for immediate interaction.
  - **File System Access**: Allows agents to perform file operations via a Master Control Program (MCP).
  - **Email Automation**: Integrated with Mailgun for automated email functionalities.
  - **Asynchronous Architecture**: Built with modern async patterns for improved performance.
  - **Production Monitoring**: Equipped with health checks and performance tracking.

## **Quick Start Guide**

### **1. Environment Setup**

```bash
# Clone the repository
git clone git@github.com:copp1723/multi_uni_merge.git
cd multi_uni_merge

# Execute the development environment setup script
./scripts/setup-dev.sh
```

### **2. Configure Environment Variables**

```bash
# Create a .env file from the example
cp .env.example .env

# Edit the .env file with your specific configuration values
# (e.g., DATABASE_URL, OPENROUTER_API_KEY, SUPERMEMORY_API_KEY)
```

### **3. Run the System**

```bash
# Start the backend server
cd backend && python main.py

# In a separate terminal, start the frontend application
cd frontend && npm run dev
```

Once both servers are running, access the application at `http://localhost:3000`. You can select an agent from the sidebar to open a dedicated chat window. Use the `@` key to mention and involve other agents in the conversation. Previous messages will be loaded to continue existing chats.

## **Repository Structure**

```
multi_uni_merge/
├── backend/                  # Python backend (Flask + SocketIO)
│   ├── services/             # Service implementations
│   ├── utils/                # Shared utilities and helpers
│   ├── main.py               # Application entry point
│   └── swarm_orchestrator.py # Core agent orchestration logic
├── frontend/                 # React frontend application
│   └── src/                  # Frontend source code
├── config/                   # Configuration files
│   ├── requirements.txt      # Python dependencies
│   ├── docker-compose.yml    # Docker deployment configuration
│   └── *.Dockerfile          # Container configurations
├── docs/                     # Project Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── TEST_RESULTS.md
└── scripts/                  # Utility scripts
    └── setup-dev.sh          # Automated environment setup script
```

## **Enhanced Agent System**

### **Communication Agent**

  - Analyzes and adopts a specific business tone for professional communication.
  - Transforms text to be professional yet approachable.
  - Generates storytelling-driven content with action-oriented outcomes.

### **Core Agents**

  - **Cathy**: Aims to provide proactive productivity partnership.
  - **DataMiner**: Focuses on business intelligence and creating data-driven narratives.
  - **Coder**: Produces human-readable and maintainable code.
  - **Creative**: Generates compelling narratives to drive engagement.
  - **Researcher**: Delivers reliable and well-sourced insights.

## **Architecture Highlights**

### **Modern Infrastructure**

  - **Asynchronous Patterns**: Utilizes `async/await` throughout the system for efficiency.
  - **Service-Oriented Architecture**: Employs a service registry for modularity.
  - **Comprehensive Error Handling**: Implements standardized error codes.
  - **Production Monitoring**: Includes health checks for system reliability.
  - **Audited Dependencies**: All dependencies have been security-audited, reporting zero vulnerabilities.

### **Service Layer**

  - **PostgreSQL Service**: Manages database connections and optimizations.
  - **OpenRouter Service**: Integrates AI models with response caching.
  - **Supermemory Service**: Facilitates cross-agent memory and knowledge sharing.
  - **MCP Filesystem**: Provides secure file system access for agents.
  - **Mailgun Service**: Enables email automation capabilities.
  - **WebSocket Service**: Manages real-time, bidirectional communication.

## **Deployment**

### **Render Deployment (Recommended)**

1.  Connect this repository to your Render account.
2.  Configure the necessary environment variables in the Render dashboard.
3.  Deploy the application using the provided Docker configuration.

### **Docker Deployment**

```bash
# Use the docker-compose file for deployment
docker-compose -f config/docker-compose.yml up -d
```

### **Manual Deployment**

For detailed, step-by-step instructions, please refer to the [DEPLOYMENT\_GUIDE.md](https://www.google.com/search?q=./docs/DEPLOYMENT_GUIDE.md).

## **Test Results**

**Test Success Rate: 100% (7/7 tests passing)**

  - Repository Structure
  - Backend Dependencies
  - Tenacity-based retry logic
  - Frontend Dependencies
  - Configuration Files
  - Documentation
  - Service Imports
  - Agent System

For a detailed breakdown of test cases and results, please see [TEST\_RESULTS.md](https://www.google.com/search?q=./docs/TEST_RESULTS.md).

## **Documentation**

  - [Deployment Guide](https://www.google.com/search?q=./docs/DEPLOYMENT_GUIDE.md): Instructions for production deployment.
  - [Development Guide](https://www.google.com/search?q=./docs/DEVELOPMENT_GUIDE.md): Information on architecture and development.
  - [Test Results](https://www.google.com/search?q=./docs/TEST_RESULTS.md): Comprehensive test documentation.
  - [Project Summary](https://www.google.com/search?q=./MISSION_ACCOMPLISHED.md): A summary of the project's completion.

## **Core Vision**

This system is designed to support the following functionalities:

  - **Chat-based Agent Interaction**: Users can interact with individual agents in dedicated chat windows with model selection.
  - **Group Collaboration**: Agents can be mentioned (`@`) to collaborate on tasks within a single conversation.
  - **Individual Agent Work**: Agents can perform assigned tasks independently.
  - **Filesystem Access**: Agents have the capability to access and operate on the local filesystem via the MCP.
  - **Cross-Agent Memory**: A persistent knowledge base is shared among all agents through Supermemory integration.

## **Platform Advantages**

This v3.0 system integrates the core strengths of its predecessors: the sophisticated swarm intelligence from the `unified` branch and the robust, production-ready infrastructure from the `multi-agent` system. It has been further enhanced with a modern asynchronous architecture, comprehensive testing, and features tailored to specific operational requirements. The result is a superior, enterprise-grade platform ready for immediate deployment.

-----

## **Support**

For questions, bug reports, or contributions, please refer to the project documentation or open an issue in this repository.
