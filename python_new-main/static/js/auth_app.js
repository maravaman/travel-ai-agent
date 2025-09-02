/**
 * 🔐 LangGraph AI System - Authentication & User Interface
 * Handles user authentication, session management, and user-specific features
 */

class AuthenticatedApp {
    constructor() {
        this.currentUser = null;
        this.authToken = localStorage.getItem('auth_token');
        this.sessionId = localStorage.getItem('session_id');
        this.apiBase = '';
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkAuthStatus();
        await this.checkOllamaStatus();
    }

    setupEventListeners() {
        // Auth form handlers
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('showRegister').addEventListener('click', (e) => this.showRegister(e));
        document.getElementById('showLogin').addEventListener('click', (e) => this.showLogin(e));
        document.getElementById('logoutBtn').addEventListener('click', (e) => this.handleLogout(e));

        // Chat form handler
        document.getElementById('chatForm').addEventListener('submit', (e) => this.handleChatSubmit(e));
        
        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickAction(e));
        });
    }

    async checkAuthStatus() {
        if (this.authToken) {
            try {
                const response = await fetch(`${this.apiBase}/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    this.currentUser = await response.json();
                    this.showMainApp();
                    await this.loadUserData();
                    return;
                } else {
                    // Token invalid, clear it
                    this.clearAuth();
                }
            } catch (error) {
                console.warn('Auth check failed:', error);
                this.clearAuth();
            }
        }
        
        this.showAuth();
    }

    showAuth() {
        document.getElementById('loginContainer').style.display = 'flex';
        document.getElementById('registerContainer').style.display = 'none';
        document.getElementById('mainContainer').style.display = 'none';
        document.getElementById('userInfo').style.display = 'none';
    }

    showMainApp() {
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('registerContainer').style.display = 'none';
        document.getElementById('mainContainer').style.display = 'flex';
        document.getElementById('userInfo').style.display = 'flex';
        
        // Update welcome message
        if (this.currentUser) {
            document.getElementById('welcomeMessage').textContent = 
                `Welcome, ${this.currentUser.username}!`;
        }
        
        // Enable chat input
        document.getElementById('chatInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
    }

    showRegister(e) {
        e.preventDefault();
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('registerContainer').style.display = 'flex';
    }

    showLogin(e) {
        e.preventDefault();
        document.getElementById('registerContainer').style.display = 'none';
        document.getElementById('loginContainer').style.display = 'flex';
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        if (!username || !password) {
            this.showToast('Please enter both username and password', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.authToken = result.token;
                this.sessionId = result.session_id;
                this.currentUser = result.user;
                
                // Store in localStorage
                localStorage.setItem('auth_token', this.authToken);
                localStorage.setItem('session_id', this.sessionId);
                
                this.showToast(`Welcome back, ${username}!`, 'success');
                this.showMainApp();
                await this.loadUserData();
            } else {
                this.showToast(result.message || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showToast('Login failed. Please try again.', 'error');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        if (!username || !email || !password) {
            this.showToast('Please fill in all fields', 'error');
            return;
        }

        if (password.length < 6) {
            this.showToast('Password must be at least 6 characters long', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.authToken = result.token;
                this.sessionId = result.session_id;
                this.currentUser = result.user;
                
                // Store in localStorage
                localStorage.setItem('auth_token', this.authToken);
                localStorage.setItem('session_id', this.sessionId);
                
                this.showToast(`Welcome, ${username}! Account created successfully.`, 'success');
                this.showMainApp();
                await this.loadUserData();
            } else {
                this.showToast(result.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showToast('Registration failed. Please try again.', 'error');
        }
    }

    async handleLogout(e) {
        e.preventDefault();
        
        try {
            await fetch(`${this.apiBase}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.warn('Logout request failed:', error);
        }
        
        this.clearAuth();
        this.clearAllUserData();
        this.showToast('Logged out successfully', 'success');
        this.showAuth();
    }

    clearAuth() {
        this.currentUser = null;
        this.authToken = null;
        this.sessionId = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('session_id');
    }

    clearAllUserData() {
        // Clear all user-specific UI elements
        const elementsTosClear = [
            'userProfile',
            'queryHistory', 
            'userStats',
            'activeAgents',
            'chatMessages'
        ];
        
        elementsTosClear.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = '';
            }
        });
        
        // Reset welcome message
        const welcomeMessage = document.getElementById('welcomeMessage');
        if (welcomeMessage) {
            welcomeMessage.textContent = 'Welcome!';
        }
    }

    async loadUserData() {
        if (!this.authToken) return;
        
        try {
            // Load user profile
            await this.loadUserProfile();
            
            // Load query history
            await this.loadQueryHistory();
            
            // Load user statistics
            await this.loadUserStats();
            
            // Load active agents
            await this.loadActiveAgents();
            
        } catch (error) {
            console.error('Failed to load user data:', error);
        }
    }

    async loadUserProfile() {
        const profileDiv = document.getElementById('userProfile');
        
        if (this.currentUser) {
            profileDiv.innerHTML = `
                <div class="profile-info">
                    <div class="profile-item">
                        <i class="fas fa-user"></i>
                        <span>${this.currentUser.username}</span>
                    </div>
                    <div class="profile-item">
                        <i class="fas fa-envelope"></i>
                        <span>${this.currentUser.email}</span>
                    </div>
                    <div class="profile-item">
                        <i class="fas fa-calendar"></i>
                        <span>Member since ${new Date(this.currentUser.created_at).toLocaleDateString()}</span>
                    </div>
                    ${this.currentUser.last_login ? `
                        <div class="profile-item">
                            <i class="fas fa-clock"></i>
                            <span>Last login: ${new Date(this.currentUser.last_login).toLocaleString()}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }
    }

    async loadQueryHistory() {
        const historyDiv = document.getElementById('queryHistory');
        
        try {
            const response = await fetch(`${this.apiBase}/auth/queries?limit=10`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const queries = await response.json();
                
                if (queries.length === 0) {
                    historyDiv.innerHTML = '<p class="no-data">No queries yet. Start asking questions!</p>';
                    return;
                }
                
                historyDiv.innerHTML = queries.map(query => `
                    <div class="query-item">
                        <div class="query-question">
                            <i class="fas fa-question-circle"></i>
                            ${query.question.length > 50 ? query.question.substring(0, 50) + '...' : query.question}
                        </div>
                        <div class="query-meta">
                            <span class="agent"><i class="fas fa-robot"></i> ${query.agent_used}</span>
                            <span class="time">${new Date(query.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                `).join('');
            } else {
                historyDiv.innerHTML = '<p class="error">Failed to load query history</p>';
            }
        } catch (error) {
            console.error('Failed to load query history:', error);
            historyDiv.innerHTML = '<p class="error">Failed to load query history</p>';
        }
    }

    async loadUserStats() {
        const statsDiv = document.getElementById('userStats');
        
        try {
            const response = await fetch(`${this.apiBase}/auth/stats`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const stats = await response.json();
                
                statsDiv.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-item">
                            <i class="fas fa-question-circle"></i>
                            <span class="stat-value">${stats.total_queries}</span>
                            <span class="stat-label">Total Queries</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-robot"></i>
                            <span class="stat-value">${Object.keys(stats.agent_usage).length}</span>
                            <span class="stat-label">Agents Used</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-chart-line"></i>
                            <span class="stat-value">${stats.total_activities}</span>
                            <span class="stat-label">Total Activities</span>
                        </div>
                    </div>
                    <div class="agent-usage">
                        <h4>Most Used Agents:</h4>
                        ${Object.entries(stats.agent_usage)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 3)
                            .map(([agent, count]) => `
                                <div class="agent-stat">
                                    <span class="agent-name">${agent}</span>
                                    <span class="agent-count">${count}</span>
                                </div>
                            `).join('')}
                    </div>
                `;
            } else {
                statsDiv.innerHTML = '<p class="error">Failed to load statistics</p>';
            }
        } catch (error) {
            console.error('Failed to load user stats:', error);
            statsDiv.innerHTML = '<p class="error">Failed to load statistics</p>';
        }
    }

    async loadActiveAgents() {
        const agentsDiv = document.getElementById('activeAgents');
        
        try {
            const response = await fetch(`${this.apiBase}/agents`);
            
            if (response.ok) {
                const data = await response.json();
                const agents = data.agents || {};
                
                if (Object.keys(agents).length === 0) {
                    agentsDiv.innerHTML = '<p class="no-data">No active agents</p>';
                    return;
                }
                
                agentsDiv.innerHTML = Object.values(agents).map(agent => `
                    <div class="agent-item">
                        <div class="agent-name">
                            <i class="fas fa-cog"></i>
                            ${agent.name || agent.id}
                        </div>
                        <div class="agent-desc">${agent.description || 'No description'}</div>
                    </div>
                `).join('');
            } else {
                agentsDiv.innerHTML = '<p class="error">Failed to load agents</p>';
            }
        } catch (error) {
            console.error('Failed to load active agents:', error);
            agentsDiv.innerHTML = '<p class="error">Failed to load agents</p>';
        }
    }

    async handleChatSubmit(e) {
        e.preventDefault();
        
        const input = document.getElementById('chatInput');
        const question = input.value.trim();
        
        if (!question) return;
        
        // Add user message to chat
        this.addMessage(question, 'user');
        
        // Clear input and show loading
        input.value = '';
        this.showLoading(true);
        
        try {
            const response = await fetch(`${this.apiBase}/run_graph`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user: this.currentUser?.username || 'User',
                    question: question
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Add AI response to chat
                this.addMessage(result.response, 'assistant', {
                    agent: result.agent,
                    edges: result.edges_traversed,
                    timestamp: result.timestamp
                });
                
                // Reload user data to update stats
                await this.loadUserStats();
                await this.loadQueryHistory();
                
            } else {
                const error = await response.json();
                this.addMessage(`Sorry, there was an error: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('Sorry, there was a network error. Please try again.', 'error');
        }
        
        this.showLoading(false);
    }

    handleQuickAction(e) {
        const query = e.target.dataset.query;
        if (query) {
            document.getElementById('chatInput').value = query;
            document.getElementById('chatForm').dispatchEvent(new Event('submit'));
        }
    }

    addMessage(content, type, metadata = {}) {
        const messagesDiv = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        let messageHTML = `<div class="message-content">${content}</div>`;
        
        if (metadata.agent) {
            messageHTML += `
                <div class="message-meta">
                    <span class="agent"><i class="fas fa-robot"></i> ${metadata.agent}</span>
                    ${metadata.edges ? `<span class="edges">Path: ${metadata.edges.join(' → ')}</span>` : ''}
                    ${metadata.timestamp ? `<span class="time">${new Date(metadata.timestamp).toLocaleTimeString()}</span>` : ''}
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        messagesDiv.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }

    async checkOllamaStatus() {
        const statusSpan = document.getElementById('ollamaStatus');
        
        try {
            const response = await fetch(`${this.apiBase}/api/ollama/status`);
            const status = await response.json();
            
            if (status.available) {
                statusSpan.innerHTML = '<i class="fas fa-circle" style="color: green;"></i> Ollama: Connected';
            } else {
                statusSpan.innerHTML = '<i class="fas fa-circle" style="color: red;"></i> Ollama: Disconnected';
            }
        } catch (error) {
            statusSpan.innerHTML = '<i class="fas fa-circle" style="color: red;"></i> Ollama: Error';
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AuthenticatedApp();
});
