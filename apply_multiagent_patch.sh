#!/bin/bash

# Apply the multi-agent collaboration patch
cd "$(dirname "$0")"

# Create the patch file
cat > multiagent_collaboration.patch << 'EOF'
diff --git a/backend/services/websocket_service.py b/backend/services/websocket_service.py
index 4eed85103528ba95847eb2a067b4644b3691b11e..b1a73961bde85b32c8c0ded773fdc3d58a4bb00d 100644
--- a/backend/services/websocket_service.py
+++ b/backend/services/websocket_service.py
@@ -447,50 +447,87 @@ class SwarmNamespace(Namespace):
 
             # Update agent status
             self.websocket_service.update_agent_status(agent_id, AgentStatus.THINKING)
 
             # Create streaming session
             session_id = str(uuid.uuid4())
             self.websocket_service.streaming_sessions[session_id] = {
                 "client_id": client_id,
                 "agent_id": agent_id,
                 "active": True,
                 "started_at": datetime.now(timezone.utc).isoformat(),
             }
 
             # Start streaming response in background thread
             thread = threading.Thread(
                 target=self.websocket_service.start_streaming_response,
                 args=(session_id, message, model),
             )
             thread.daemon = True
             thread.start()
 
         except Exception as e:
             logger.error(f"❌ Error handling agent message: {e}")
             emit("error", {"message": f"Error processing message: {str(e)}"})
 
+    def on_swarm_message(self, data):
+        """Handle multi-agent message via orchestrator"""
+        try:
+            client_id = request.sid
+            message_content = data.get("message")
+            agent_ids = data.get("agent_ids")
+
+            if not message_content:
+                emit("error", {"message": "Missing message"})
+                return
+
+            # Derive agent IDs from mentions if not provided
+            if not agent_ids and self.websocket_service.orchestrator:
+                agent_ids = self.websocket_service.orchestrator.extract_mentions(message_content)
+
+            if self.websocket_service.orchestrator:
+                import asyncio
+                try:
+                    responses = asyncio.run(
+                        self.websocket_service.orchestrator.process_message(
+                            message_content,
+                            agent_ids=agent_ids,
+                        )
+                    )
+                except Exception as err:
+                    logger.error(f"❌ Swarm processing error: {err}")
+                    emit("error", {"message": str(err)})
+                    return
+
+                emit("swarm_responses", {"responses": responses}, room=client_id)
+            else:
+                emit("error", {"message": "Orchestrator not available"})
+
+        except Exception as e:
+            logger.error(f"❌ Error handling swarm message: {e}")
+            emit("error", {"message": f"Error processing message: {str(e)}"})
+
     def on_stop_stream(self, data):
         """Handle stream stop request"""
         try:
             session_id = data.get("session_id")
             if session_id in self.websocket_service.streaming_sessions:
                 self.websocket_service.streaming_sessions[session_id]["active"] = False
                 logger.info(f"🛑 Stream stopped: {session_id}")
                 emit("stream_stopped", {"session_id": session_id})
         except Exception as e:
             logger.error(f"❌ Error stopping stream: {e}")
 
     def on_join_room(self, data):
         """Handle room join request"""
         try:
             room_id = data.get("room_id")
             if room_id:
                 join_room(room_id)
                 self.websocket_service.active_rooms[
                     room_id
                 ] = self.websocket_service.active_rooms.get(room_id, [])
                 if request.sid not in self.websocket_service.active_rooms[room_id]:
                     self.websocket_service.active_rooms[room_id].append(request.sid)
                 emit("room_joined", {"room_id": room_id})
         except Exception as e:
             logger.error(f"❌ Error joining room: {e}")
diff --git a/backend/swarm_orchestrator.py b/backend/swarm_orchestrator.py
index 9b02b93fdb6b7d213737c31ea61b7a5d8afc099b..8aec1b35903ce2f4f8429ce1205cd31550f546c7 100644
--- a/backend/swarm_orchestrator.py
+++ b/backend/swarm_orchestrator.py
@@ -242,52 +242,62 @@ class SwarmOrchestrator:
             score = 0.0
             
             # Capability matching
             if required_capabilities:
                 matching_caps = [cap for cap in agent.capabilities 
                                if cap.name in required_capabilities]
                 if matching_caps:
                     avg_confidence = sum(cap.confidence_level for cap in matching_caps) / len(matching_caps)
                     score += avg_confidence * 0.6
             
             # Performance history
             score += (agent.performance.success_rate / 100) * 0.3
             
             # Current load (prefer less busy agents)
             if agent.status == "idle":
                 score += 0.1
             
             agent_scores[agent_id] = score
         
         if not agent_scores:
             return None
         
         # Select agent with highest score
         best_agent_id = max(agent_scores, key=agent_scores.get)
         return self.agents[best_agent_id]
-    
-    async def process_message(self, message: str, agent_ids: List[str] = None, 
+
+    def extract_mentions(self, message: str) -> List[str]:
+        """Extract agent mentions from a message."""
+        mentions = []
+        message_lower = message.lower()
+        for aid, agent in self.agents.items():
+            name_token = agent.name.lower().replace(" ", "")
+            if f"@{aid.lower()}" in message_lower or f"@{name_token}" in message_lower:
+                mentions.append(aid)
+        return list(dict.fromkeys(mentions))
+
+    async def process_message(self, message: str, agent_ids: List[str] = None,
                             conversation_id: str = None) -> List[Dict[str, Any]]:
         """
         Process a message through the swarm with enhanced coordination
         
         Args:
             message: The message to process
             agent_ids: Specific agents to involve (optional)
             conversation_id: Conversation identifier
             
         Returns:
             List of agent responses
         """
         responses = []
         
         try:
             # Determine which agents to involve
             if agent_ids:
                 selected_agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
             else:
                 # Auto-select based on message content
                 selected_agents = await self._auto_select_agents(message)
             
             if not selected_agents:
                 logger.warning("No suitable agents found for message")
                 return responses
diff --git a/backend/test_orchestrator.py b/backend/test_orchestrator.py
new file mode 100644
index 0000000000000000000000000000000000000000..0c35c9cb1106999359523d8e2099329b8823800f
--- /dev/null
+++ b/backend/test_orchestrator.py
@@ -0,0 +1,16 @@
+import pytest
+from swarm_orchestrator import SwarmOrchestrator
+
+@pytest.mark.asyncio
+async def test_process_message_multiple_agents(monkeypatch):
+    orchestrator = SwarmOrchestrator()
+
+    async def dummy_get_agent_response(agent, message, conversation_id=None):
+        return {"agent_id": agent.id, "content": f"hi from {agent.name}"}
+
+    monkeypatch.setattr(orchestrator, "_get_agent_response", dummy_get_agent_response)
+
+    responses = await orchestrator.process_message("hello", agent_ids=["comms", "coder"])
+    assert len(responses) == 2
+    ids = {r["agent_id"] for r in responses}
+    assert ids == {"comms", "coder"}
diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
index 1e6cc7b32dbc797f560bb0d4ba7c509c81d5481c..808002a0dfc5c31d206fa536ea40b2ea2f903a62 100644
--- a/frontend/src/App.jsx
+++ b/frontend/src/App.jsx
@@ -1,125 +1,163 @@
-import React, { useState, useEffect } from 'react';
+import React, { useState, useEffect, useRef } from 'react';
+import { io } from 'socket.io-client';
 import { 
   Layers, Settings, Cpu, CheckCircle, AlertTriangle, 
   MessageSquare, Mail, Code, Calendar, Wrench, Smile,
   ChevronDown, Sun, Send
 } from 'lucide-react';
 
 // Dynamically determine API URL based on current location
 const API_BASE_URL = (() => {
   // If VITE_API_URL is set, use it
   if (import.meta.env.VITE_API_URL) {
     return import.meta.env.VITE_API_URL;
   }
   
   // In production, use the same origin as the frontend
   if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
     return window.location.origin;
   }
   
   // In development, use localhost:5000
   return 'http://localhost:5000';
 })();
 
 function App() {
   // Core State
   const [agents, setAgents] = useState([]);
   const [selectedAgent, setSelectedAgent] = useState(null);
   const [message, setMessage] = useState('');
   const [notifications, setNotifications] = useState([]);
+  const [chatMessages, setChatMessages] = useState([]);
+  const socketRef = useRef(null);
   const [selectedModel, setSelectedModel] = useState('GPT-4o');
   const [showModelDropdown, setShowModelDropdown] = useState(false);
   const [modelOptions, setModelOptions] = useState([]);
   const [transformText, setTransformText] = useState('');
   const [isTransforming, setIsTransforming] = useState(false);
 
   // Load agents on mount
   useEffect(() => {
     loadAgents();
     loadModels();
   }, []);
 
   useEffect(() => {
     if (selectedAgent) {
       fetchAgentConfig(selectedAgent.id);
     }
   }, [selectedAgent]);
 
   const loadAgents = async () => {
     try {
       const response = await fetch(`${API_BASE_URL}/api/agents`);
       const data = await response.json();
       setAgents(data.data || []);
     } catch (error) {
       console.error('Error loading agents:', error);
       addNotification('Failed to load agents', 'error');
     }
   };
 
   const loadModels = async () => {
     try {
       const response = await fetch(`${API_BASE_URL}/api/models`);
       const data = await response.json();
       setModelOptions(data.data || []);
     } catch (error) {
       console.error('Error loading models:', error);
     }
   };
 
+  // Initialize WebSocket connection
+  useEffect(() => {
+    socketRef.current = io(`${API_BASE_URL}/swarm`);
+    socketRef.current.on('swarm_responses', (data) => {
+      const responses = data.responses || [];
+      setChatMessages((prev) => [...prev, ...responses.map(r => ({ ...r, sender: 'agent' }))]);
+    });
+    socketRef.current.on('connect_error', () => {
+      addNotification('WebSocket connection failed', 'error');
+    });
+    return () => {
+      socketRef.current?.disconnect();
+    };
+  }, []);
+
   const fetchAgentConfig = async (id) => {
     try {
       const response = await fetch(`${API_BASE_URL}/api/agents/${id}/config`);
       const data = await response.json();
       if (data.data && data.data.current_model) {
         setSelectedModel(data.data.current_model);
       }
     } catch (error) {
       console.error('Error fetching agent config:', error);
     }
   };
 
   const addNotification = (message, type = 'info') => {
     const notification = {
       id: Date.now(),
       message,
       type,
       timestamp: new Date()
     };
     setNotifications(prev => [...prev, notification]);
     
     // Auto remove after 5 seconds
     setTimeout(() => {
       setNotifications(prev => prev.filter(n => n.id !== notification.id));
     }, 5000);
   };
 
   const handleSendMessage = () => {
     if (message.trim()) {
-      console.log('Sending message:', message);
+      const content = message.trim();
+      setChatMessages(prev => [...prev, { sender: 'user', content }]);
+
+      // Parse @mentions to determine agent IDs
+      const mentionRegex = /@(\w+)/g;
+      const found = content.match(mentionRegex) || [];
+      const agentIds = found
+        .map(m => m.slice(1).toLowerCase())
+        .map(name => {
+          const agent = agents.find(a =>
+            a.name.toLowerCase().replace(/\s+/g, '') === name ||
+            a.id.toLowerCase() === name
+          );
+          return agent ? agent.id : null;
+        })
+        .filter(Boolean);
+
+      socketRef.current?.emit('swarm_message', {
+        message: content,
+        agent_ids: agentIds.length > 0 ? agentIds : [selectedAgent?.id].filter(Boolean)
+      });
+
       setMessage('');
-      addNotification('Message sent!', 'success');
     }
   };
 
   const handleKeyPress = (e) => {
     if (e.key === 'Enter' && !e.shiftKey) {
       e.preventDefault();
       handleSendMessage();
     }
   };
 
   const getAgentIcon = (agentName) => {
     const iconMap = {
       'Communication Agent': MessageSquare,
       'Cathy': Smile,
       'DataMiner': Cpu,
       'Coder': Code,
       'Creative': Mail,
       'Researcher': CheckCircle
     };
     return iconMap[agentName] || MessageSquare;
   };
 
   const handleTransform = async () => {
     if (!transformText.trim()) {
       addNotification('Please enter text to transform', 'error');
@@ -374,59 +412,62 @@ function App() {
               <div className="grid grid-cols-3 gap-4 max-w-3xl mx-auto">
                 <div className="p-6 bg-gray-50 border border-gray-100 rounded-xl hover:bg-gray-100 hover:border-blue-200 hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                   <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                     <MessageSquare className="w-6 h-6 text-blue-500" />
                   </div>
                   <h3 className="font-semibold text-gray-900 mb-2">Communications</h3>
                   <p className="text-sm text-gray-600">Transform text into clear, professional communication</p>
                 </div>
                 <div className="p-6 bg-gray-50 border border-gray-100 rounded-xl hover:bg-gray-100 hover:border-blue-200 hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                   <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                     <Mail className="w-6 h-6 text-blue-500" />
                   </div>
                   <h3 className="font-semibold text-gray-900 mb-2">Email Assistant</h3>
                   <p className="text-sm text-gray-600">Professional email composition and strategy</p>
                 </div>
                 <div className="p-6 bg-gray-50 border border-gray-100 rounded-xl hover:bg-gray-100 hover:border-blue-200 hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                   <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                     <Code className="w-6 h-6 text-blue-500" />
                   </div>
                   <h3 className="font-semibold text-gray-900 mb-2">Code Assistant</h3>
                   <p className="text-sm text-gray-600">Clean code generation and technical solutions</p>
                 </div>
               </div>
             </div>
           ) : (
-            <div className="text-center">
-              <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
-                {React.createElement(getAgentIcon(selectedAgent.name), { 
-                  className: "w-8 h-8 text-gray-400" 
-                })}
-              </div>
-              <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to collaborate!</h3>
-              <p className="text-gray-500 mb-4">Start a conversation with {selectedAgent.name}.</p>
-              <p className="text-sm text-gray-400">💡 Tip: Use @mentions to bring specific agents into the conversation</p>
+            <div className="flex flex-col w-full p-4 overflow-y-auto space-y-4">
+              {chatMessages.map((msg, idx) => (
+                <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
+                  <div className={`px-3 py-2 rounded-lg max-w-xl break-words ${msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'}`}>
+                    {msg.agent_name && <strong className="mr-2">{msg.agent_name}:</strong>}
+                    {msg.content}
+                  </div>
+                </div>
+              ))}
+              {chatMessages.length === 0 && (
+                <div className="text-center text-gray-400">Start chatting with {selectedAgent.name}. Use @mentions to involve other agents.</div>
+              )}
             </div>
           )}
         </div>
 
         {/* Message Input */}
         {selectedAgent && (
           <div className="p-5 bg-white border-t border-gray-200">
             <div className="flex gap-3 items-end">
               <div className="flex-1">
                 <textarea
                   value={message}
                   onChange={(e) => setMessage(e.target.value)}
                   onKeyPress={handleKeyPress}
                   placeholder="Type your message... Use @ to mention other agents"
                   className="w-full min-h-[44px] max-h-[120px] px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:border-blue-500 focus:bg-white transition-colors text-sm"
                   rows="1"
                 />
               </div>
               <button
                 onClick={handleSendMessage}
                 className="w-11 h-11 bg-blue-500 text-white rounded-xl flex items-center justify-center hover:bg-blue-600 hover:-translate-y-0.5 transition-all duration-200 shadow-md"
               >
                 <Send className="w-5 h-5" />
               </button>
             </div>
EOF

# Apply the patch
echo "Applying multi-agent collaboration patch..."
git apply --3way multiagent_collaboration.patch

if [ $? -eq 0 ]; then
    echo "✅ Patch applied successfully!"
    rm multiagent_collaboration.patch
else
    echo "❌ Failed to apply patch. The patch file is saved as multiagent_collaboration.patch"
    echo "You may need to apply changes manually."
fi
