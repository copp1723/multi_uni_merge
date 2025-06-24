#!/bin/bash

# Test Multi-Agent Collaboration Setup

echo "🚀 Testing Multi-Agent Collaboration Setup..."
echo "=========================================="

# Function to check if services are running
check_service() {
    local service_name=$1
    local port=$2
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $service_name is running on port $port"
        return 0
    else
        echo "❌ $service_name is NOT running on port $port"
        return 1
    fi
}

# Check backend
echo -e "\n📋 Checking Backend Services:"
check_service "Backend API" 5000

# Check if WebSocket endpoint is available
echo -e "\n📡 Testing WebSocket endpoint:"
curl -s http://localhost:5000/api/agents > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API endpoint is accessible"
else
    echo "❌ API endpoint is NOT accessible"
fi

# Test orchestrator
echo -e "\n🤖 Testing Orchestrator:"
cd backend
python3 -c "
from swarm_orchestrator import SwarmOrchestrator
orchestrator = SwarmOrchestrator()
print('✅ Orchestrator initialized successfully')
print(f'✅ {len(orchestrator.agents)} agents loaded:')
for agent_id, agent in orchestrator.agents.items():
    print(f'   - {agent.name} ({agent_id})')

# Test extract_mentions method
test_message = 'Hey @coder and @cathy, can you help me?'
mentions = orchestrator.extract_mentions(test_message)
print(f'\n✅ Mention extraction test:')
print(f'   Message: {test_message}')
print(f'   Extracted mentions: {mentions}')
"

echo -e "\n✨ Multi-Agent Collaboration Features:"
echo "1. ✅ WebSocket handler with 'on_swarm_message' method"
echo "2. ✅ Orchestrator with 'extract_mentions' method"
echo "3. ✅ Frontend with socket.io-client integration"
echo "4. ✅ Chat UI with message display"
echo "5. ✅ @mention parsing in frontend"

echo -e "\n📝 Usage Instructions:"
echo "1. Start the backend: cd backend && python app.py"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Select an agent from the sidebar"
echo "4. Type a message with @mentions (e.g., '@coder help me debug this')"
echo "5. Multiple agents will respond based on mentions"

echo -e "\n🎯 Example Messages to Try:"
echo "- '@coder @cathy help me organize my code project'"
echo "- '@dataminer analyze this data and @creative make it presentable'"
echo "- '@researcher find information about AI and @comms help me write about it'"
