class MultiAgentLangGraphApp {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.currentUser = null;
        this.ws = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        
        if (this.token) {
            this.validateToken();
        } else {
            this.showAuthForms();
        }
        
        this.checkOllamaStatus();
    }
    
    bindEvents() {
        // Auth form events
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('showRegister').addEventListener('click', (e) => this.showRegisterForm(e));
        document.getElementById('showLogin').addEventListener('click', (e) => this.showLoginForm(e));
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
        
        // Chat form events
        document.getElementById('chatForm').addEventListener('submit', (e) => this.handleChatSubmit(e));
        
        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickAction(e));
        });
        
        // Enter key in chat input
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleChatSubmit(e);
            }
        });
    }
    
    async validateToken() {
        try {
            const response = await this.apiCall('/auth/me', 'GET');
            if (response.ok) {
                const user = await response.json();
                this.currentUser = user;
                this.showMainApp();
            } else {
                this.clearAuth();
                this.showAuthForms();
            }
        } catch (error) {
            console.error('Token validation failed:', error);
            this.clearAuth();
            this.showAuthForms();
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const loginData = {
            username: formData.get('username'),
            password: formData.get('password')
        };
        
        try {
            this.showLoading(true);
            const response = await this.apiCall('/auth/login', 'POST', loginData);
            
            if (response.ok) {
                const tokenData = await response.json();
                this.token = tokenData.access_token;
                localStorage.setItem('auth_token', this.token);
                
                // Get user info and recent usage
                await this.validateToken();
                this.showToast('Login successful!', 'success');
            } else {
                const error = await response.json();
                this.showToast(error.detail || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showToast('Login failed: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const registerData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password')
        };
        
        try {
            this.showLoading(true);
            const response = await this.apiCall('/auth/register', 'POST', registerData);
            
            if (response.ok) {
                this.showToast('Registration successful! Please login.', 'success');
                this.showLoginForm();
                // Clear form
                e.target.reset();
            } else {
                const error = await response.json();
                this.showToast(error.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showToast('Registration failed: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    handleLogout() {
        this.clearAuth();
        this.showAuthForms();
        this.showToast('Logged out successfully', 'info');
    }
    
    clearAuth() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('auth_token');
    }
    
    showAuthForms() {
        document.getElementById('loginContainer').style.display = 'flex';
        document.getElementById('registerContainer').style.display = 'none';
        document.getElementById('mainContainer').style.display = 'none';
        document.getElementById('userInfo').style.display = 'none';
    }
    
    showRegisterForm(e) {
        if (e) e.preventDefault();
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('registerContainer').style.display = 'flex';
    }
    
    showLoginForm(e) {
        if (e) e.preventDefault();
        document.getElementById('loginContainer').style.display = 'flex';
        document.getElementById('registerContainer').style.display = 'none';
    }
    
    async showMainApp() {
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('registerContainer').style.display = 'none';
        document.getElementById('mainContainer').style.display = 'flex';
        document.getElementById('userInfo').style.display = 'flex';
        
        // Update welcome message
        document.getElementById('welcomeMessage').textContent = `Welcome, ${this.currentUser.username}!`;
        
        // Enable chat input
        document.getElementById('chatInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        
        // Load user session data
        await this.loadUserSession();
    }
    
    async loadUserSession() {
        try {
            const response = await this.apiCall('/auth/session', 'GET');
            if (response.ok) {
                const sessionData = await response.json();
                this.displayRecentUsage(sessionData.recent_interactions);
                this.displayActiveAgents(sessionData.active_agents);
            }
        } catch (error) {
            console.error('Failed to load user session:', error);
        }
    }
    
    displayRecentUsage(interactions) {
        const container = document.getElementById('recentUsage');
        if (!interactions || interactions.length === 0) {
            container.innerHTML = '<p class="loading">No recent interactions</p>';
            return;
        }
        
        const html = interactions.map(interaction => {
            if (interaction.source_type === 'orchestration') {
                // Multi-agent orchestration display
                const agents = JSON.parse(interaction.agents_used || '[]');
                return `
                    <div class="usage-item multi-agent-item">
                        <h4>🚀 Multi-Agent: ${agents.join(', ')}</h4>
                        <p>${this.truncate(interaction.query, 50)}</p>
                        <div class="usage-time">${this.formatTime(interaction.timestamp)}</div>
                        <div class="orchestration-badge">${interaction.routing_strategy}</div>
                    </div>
                `;
            } else {
                // Single agent interaction
                return `
                    <div class="usage-item">
                        <h4>${this.getAgentIcon(interaction.agent_name)} ${interaction.agent_name}</h4>
                        <p>${this.truncate(interaction.query, 50)}</p>
                        <div class="usage-time">${this.formatTime(interaction.timestamp)}</div>
                    </div>
                `;
            }
        }).join('');
        
        container.innerHTML = html;
    }
    
    displayActiveAgents(agents) {
        const container = document.getElementById('activeAgents');
        if (!agents || agents.length === 0) {
            container.innerHTML = '<p class="loading">No active agents</p>';
            return;
        }
        
        const agentDescriptions = {
            'SearchAgent': 'Vector similarity search',
            'ScenicLocationFinder': 'Scenic location discovery',
            'ForestAnalyzer': 'Forest ecosystem analysis',
            'WaterBodyAnalyzer': 'Water body analysis',
            'MultiAgentOrchestrator': 'Multi-agent coordination'
        };
        
        const html = agents.map(agent => `
            <div class="agent-item">
                <h4>${this.getAgentIcon(agent)} ${agent}</h4>
                <p>${agentDescriptions[agent] || 'AI Agent'}</p>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    getAgentIcon(agentName) {
        const icons = {
            'ScenicLocationFinder': '🏔️',
            'ForestAnalyzer': '🌲',
            'WaterBodyAnalyzer': '💧',
            'SearchAgent': '🔍',
            'MultiAgentOrchestrator': '🚀'
        };
        return icons[agentName] || '🤖';
    }
    
    async handleChatSubmit(e) {
        e.preventDefault();
        
        const input = document.getElementById('chatInput');
        const query = input.value.trim();
        
        if (!query) return;
        
        // Clear input and disable while processing
        input.value = '';
        this.setChatInputState(false);
        
        // Add user message to chat
        this.addUserMessage(query);
        
        try {
            this.showLoading(true);
            
            const response = await this.apiCall('/ai/chat', 'POST', {
                user: this.currentUser.username,
                user_id: this.currentUser.id,
                question: query
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addBotResponse(result);
                
                // Refresh sidebar data
                await this.loadUserSession();
            } else {
                const error = await response.json();
                this.addErrorMessage(`Error: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addErrorMessage(`Error: ${error.message}`);
        } finally {
            this.showLoading(false);
            this.setChatInputState(true);
        }
    }
    
    handleQuickAction(e) {
        const query = e.target.getAttribute('data-query');
        if (query) {
            document.getElementById('chatInput').value = query;
            this.handleChatSubmit(new Event('submit'));
        }
    }
    
    addUserMessage(content) {
        const chatContainer = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>👤 You</strong>
                <span class="timestamp">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    addBotResponse(data) {
        const chatContainer = document.getElementById('chatMessages');
        
        // Check if it's a multi-agent response
        if (data.multi_agent_responses && data.multi_agent_responses.length > 0) {
            this.addMultiAgentResponse(data);
        } else {
            this.addSingleAgentResponse(data);
        }
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    addMultiAgentResponse(data) {
        const chatContainer = document.getElementById('chatMessages');
        
        // Add simple orchestration header - minimized to focus on content
        const orchestrationElement = document.createElement('div');
        orchestrationElement.className = 'message orchestration-header';
        orchestrationElement.innerHTML = `
            <div class="orchestration-banner">
                <div class="orchestration-title">
                    <h3>🚀 Multi-Agent Response</h3>
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="orchestration-stats">
                    <span class="agents-count">${data.multi_agent_responses.length} specialists responded</span>
                    <span class="processing-time">Total: ${data.processing_time?.toFixed(3) || '0'}s</span>
                </div>
            </div>
        `;
        chatContainer.appendChild(orchestrationElement);
        
        // Add each agent response - FIXED TO SHOW ACTUAL CONTENT
        data.multi_agent_responses.forEach((agentResponse, index) => {
            const agentElement = document.createElement('div');
            agentElement.className = `message agent-response agent-${agentResponse.agent.toLowerCase()}`;
            
            let displayContent = agentResponse.response;
            let responseClass = 'response-text';
            let isJsonResponse = false;
            
            // Check if response is JSON and format accordingly
            try {
                const parsed = JSON.parse(agentResponse.response);
                displayContent = JSON.stringify(parsed, null, 2);
                responseClass = 'response-json';
                isJsonResponse = true;
            } catch {
                // Not JSON, format as HTML for better display
                displayContent = this.formatTextResponse(agentResponse.response);
                responseClass = 'response-content';
            }
            
            const agentIcon = this.getAgentIcon(agentResponse.agent);
            
            agentElement.innerHTML = `
                <div class="agent-header">
                    <div class="agent-info">
                        <h4>${agentIcon} ${agentResponse.agent}</h4>
                        <span class="agent-type-badge">${agentResponse.ollama_used ? '🤖 AI-Powered' : '🎭 Demo Mode'}</span>
                    </div>
                    <div class="agent-meta">
                        <span class="processing-time">${agentResponse.processing_time?.toFixed(3) || '0'}s</span>
                        <span class="timestamp">${new Date(agentResponse.timestamp).toLocaleTimeString()}</span>
                    </div>
                </div>
                <div class="agent-content">
                    ${isJsonResponse ? 
                        `<pre class="${responseClass}">${displayContent}</pre>` : 
                        `<div class="${responseClass}">${displayContent}</div>`
                    }
                </div>
                <div class="agent-footer">
                    <small>
                        Response Length: ${agentResponse.response_length || agentResponse.response.length} chars
                        ${agentResponse.error ? ' | ❌ Error occurred' : ' | ✅ Success'}
                    </small>
                </div>
            `;
            
            chatContainer.appendChild(agentElement);
        });
        
        // Add minimal summary footer (collapsed by default)
        const summaryElement = document.createElement('div');
        summaryElement.className = 'message orchestration-summary';
        summaryElement.style.fontSize = '0.85rem';
        summaryElement.style.opacity = '0.8';
        summaryElement.innerHTML = `
            <div class="summary-content">
                <details>
                    <summary style="cursor: pointer; padding: 0.5rem; background: rgba(0,0,0,0.05); border-radius: 5px;">
                        📊 Processing Details (${data.multi_agent_responses.length} agents, ${data.processing_time?.toFixed(2)}s total)
                    </summary>
                    <div style="padding: 0.8rem 0;">
                        <p><strong>Orchestration:</strong> ${data.orchestration?.successful_agents || data.multi_agent_responses.length} successful responses</p>
                        ${data.orchestration_id ? `<p><strong>ID:</strong> ${data.orchestration_id}</p>` : ''}
                        <div class="routing-scores">
                            <strong>🎯 Agent Selection Scores:</strong>
                            ${Object.entries(data.orchestration?.routing_scores || {}).map(([agent, score]) => 
                                `<span class="score-badge">${this.getAgentIcon(agent)} ${agent}: ${score}</span>`
                            ).join('')}
                        </div>
                    </div>
                </details>
            </div>
        `;
        chatContainer.appendChild(summaryElement);
    }
    
    addSingleAgentResponse(data) {
        const chatContainer = document.getElementById('chatMessages');
        const responseElement = document.createElement('div');
        responseElement.className = `message ai-message agent-${(data.agent || '').toLowerCase()}`;
        
        let displayContent = data.response;
        let responseClass = 'response-text';
        
        // Check if response is JSON and format accordingly
        try {
            const parsed = JSON.parse(data.response);
            displayContent = JSON.stringify(parsed, null, 2);
            responseClass = 'response-json';
        } catch {
            // Not JSON, keep as text with line break formatting
            displayContent = data.response.replace(/\n/g, '<br>');
        }
        
        const agentIcon = this.getAgentIcon(data.agent);
        
        responseElement.innerHTML = `
            <div class="message-header">
                <div class="agent-info">
                    <h4>${agentIcon} ${data.agent || 'AI Assistant'}</h4>
                    <span class="strategy-badge">${data.orchestration?.strategy || 'single_agent'}</span>
                </div>
                <div class="agent-meta">
                    <span class="processing-time">${data.processing_time?.toFixed(3) || '0'}s</span>
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
            <div class="message-content">
                <${responseClass === 'response-json' ? 'pre' : 'div'} class="${responseClass}">${displayContent}</${responseClass === 'response-json' ? 'pre' : 'div'}>
            </div>
            <div class="message-footer">
                <small>
                    Ollama: ${data.ollama_used ? '✅ Active' : '❌ Mock'} | 
                    Length: ${data.response_length || data.response.length} chars
                    ${data.orchestration ? ` | Routing: ${JSON.stringify(data.orchestration.routing_scores || {})}` : ''}
                </small>
            </div>
        `;
        
        chatContainer.appendChild(responseElement);
    }
    
    addErrorMessage(content) {
        const chatContainer = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = 'message error-message';
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>❌ Error</strong>
                <span class="timestamp">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    setChatInputState(enabled) {
        document.getElementById('chatInput').disabled = !enabled;
        document.getElementById('sendBtn').disabled = !enabled;
    }
    
    async checkOllamaStatus() {
        try {
            const response = await fetch('/api/ollama/status');
            const status = await response.json();
            
            const statusElement = document.getElementById('ollamaStatus');
            const statusText = statusElement.querySelector('span');
            
            if (status.available) {
                statusElement.className = 'status-indicator connected';
                statusText.textContent = 'Connected';
            } else {
                statusElement.className = 'status-indicator error';
                statusText.textContent = 'Using Mock Responses';
            }
        } catch (error) {
            const statusElement = document.getElementById('ollamaStatus');
            const statusText = statusElement.querySelector('span');
            statusElement.className = 'status-indicator error';
            statusText.textContent = 'Error';
        }
        
        // Check again in 30 seconds
        setTimeout(() => this.checkOllamaStatus(), 30000);
    }
    
    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        return fetch(endpoint, options);
    }
    
    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
    
    truncate(str, length) {
        return str.length > length ? str.substring(0, length) + '...' : str;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            return `${Math.floor(diff / 60000)}m ago`;
        } else if (diff < 86400000) { // Less than 1 day
            return `${Math.floor(diff / 3600000)}h ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    formatTextResponse(text) {
        // Convert text response to HTML with proper formatting
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')            // Italic text
            .replace(/#{1,6}\s(.+)/g, '<h3>$1</h3>')        // Headers
            .replace(/^-\s(.+)/gm, '<li>$1</li>')           // List items
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')      // Wrap lists
            .replace(/🏔️|🌲|💧|🔍|🚀|🌄|🏞️|🌊|🦌|🏖️|💦|🌍|🐯|⚠️|🌱|📸|🎯|✅|❌|🤖|🔧|⏰/g, '<span class="emoji">$&</span>'); // Style emojis
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MultiAgentLangGraphApp();
});
