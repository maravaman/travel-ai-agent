class LangGraphApp {
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
                
                // Store user info from login response
                this.currentUser = tokenData.user;
                this.showMainApp();
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
            container.innerHTML = '<p class=\"loading\">No recent interactions</p>';
            return;
        }
        
        const html = interactions.map(interaction => `
            <div class=\"usage-item\">
                <h4>${interaction.agent_name}</h4>
                <p>${this.truncate(interaction.query, 50)}</p>
                <div class=\"usage-time\">${this.formatTime(interaction.timestamp)}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    displayActiveAgents(agents) {
        const container = document.getElementById('activeAgents');
        if (!agents || agents.length === 0) {
            container.innerHTML = '<p class=\"loading\">No active agents</p>';
            return;
        }
        
        const agentDescriptions = {
            'SearchAgent': 'Vector similarity search',
            'ScenicLocationFinder': 'Scenic location discovery',
            'ForestAnalyzer': 'Forest ecosystem analysis',
            'WaterBodyAnalyzer': 'Water body analysis',
            'OrchestratorAgent': 'Query routing and orchestration'
        };
        
        const html = agents.map(agent => `
            <div class=\"agent-item\">
                <h4>${agent}</h4>
                <p>${agentDescriptions[agent] || 'AI Agent'}</p>
            </div>
        `).join('');
        
        container.innerHTML = html;
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
        this.addMessage(query, 'user');
        
        try {
            this.showLoading(true);
            
            const response = await this.apiCall('/run_graph', 'POST', {
                user: this.currentUser.username,
                question: query
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addMessage(result.response, 'bot', result.agent, result.orchestration);
                
                // Refresh sidebar data
                await this.loadUserSession();
            } else {
                const error = await response.json();
                this.addMessage(`Error: ${error.detail || 'Unknown error'}`, 'bot', 'Error');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage(`Error: ${error.message}`, 'bot', 'Error');
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
    
    addMessage(content, type, agent = null, orchestration = null) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        let messageHTML = '';
        
        if (type === 'bot' && agent) {
            messageHTML += `
                <div class=\"message-header\">
                    <span class=\"agent-badge\">${agent}</span>
                    <span>${new Date().toLocaleTimeString()}</span>
                </div>
            `;
        }
        
        messageHTML += `<div class=\"message-content\">${this.formatMessageContent(content)}</div>`;
        
        if (orchestration) {
            messageHTML += `
                <div class=\"orchestration-info\">
                    <strong>Orchestration:</strong> ${orchestration.strategy} 
                    ${orchestration.selected_agent ? `→ ${orchestration.selected_agent}` : ''}
                    ${orchestration.agents ? `→ ${orchestration.agents.join(', ')}` : ''}
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatMessageContent(content) {
        // Check if content is JSON
        try {
            const parsed = JSON.parse(content);
            return `<pre class=\"json-response\">${JSON.stringify(parsed, null, 2)}</pre>`;
        } catch {
            // Not JSON, format as regular text with line breaks
            return content.replace(/\\n/g, '<br>').replace(/\\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
        }
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
                statusText.textContent = 'Disconnected';
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
            <i class=\"fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}\"></i>
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
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LangGraphApp();
});
