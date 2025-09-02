# 📋 **Client Guide: Adding New Agents via JSON**

## 🎯 **For Clients Who Want Zero Programming**

This guide shows you how to add new agents to your LangGraph Multi-Agent System using **only JSON configuration** - no Python coding required!

---

## 🚀 **Quick Start Process**

### **Step 1: Open Configuration File**
Open `core/agents.json` in any text editor (Notepad, VS Code, etc.)

### **Step 2: Add Your Agent**
Copy one of the templates below and add it to the `agents` array

### **Step 3: Save and Restart**
Save the file and restart your system - that's it!

---

## 📝 **Agent Templates**

### **🔹 Basic Agent Template**
```json
{
  "id": "YourAgentName",
  "name": "Your Agent Display Name", 
  "description": "Brief description of what your agent does",
  "capabilities": ["capability1", "capability2", "capability3"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "priority": 2,
  "system_prompt_template": "You are a [role]. Provide [specific services]. Focus on [key areas]."
}
```

### **🔹 Business Agent Template**
```json
{
  "id": "BusinessAdvisorAgent",
  "name": "Business Advisory Agent",
  "description": "Provides business advice and strategic insights",
  "capabilities": ["business_analysis", "strategy_planning", "market_research", "financial_advice"],
  "keywords": ["business", "strategy", "market", "analysis", "planning", "finance", "profit", "investment"],
  "priority": 2,
  "system_prompt_template": "You are a business consultant and strategic advisor. Provide practical business advice, market insights, and strategic planning guidance. Be professional and data-driven in your recommendations."
}
```

### **🔹 Health Agent Template**
```json
{
  "id": "HealthWellnessAgent", 
  "name": "Health & Wellness Agent",
  "description": "Provides health, fitness, and wellness guidance",
  "capabilities": ["health_advice", "fitness_planning", "nutrition_guidance", "wellness_coaching"],
  "keywords": ["health", "fitness", "nutrition", "wellness", "exercise", "diet", "medical", "healthcare"],
  "priority": 2,
  "system_prompt_template": "You are a health and wellness expert. Provide evidence-based health advice, fitness guidance, and wellness recommendations. Always emphasize consulting healthcare professionals for medical concerns."
}
```

### **🔹 Technology Agent Template**
```json
{
  "id": "TechSupportAgent",
  "name": "Technology Support Agent", 
  "description": "Provides technology help and IT support",
  "capabilities": ["tech_support", "troubleshooting", "software_help", "hardware_guidance"],
  "keywords": ["tech", "technology", "computer", "software", "hardware", "IT", "support", "troubleshoot"],
  "priority": 2,
  "system_prompt_template": "You are a technology expert and IT support specialist. Provide clear, step-by-step technical solutions and troubleshooting guidance. Make complex technical concepts easy to understand."
}
```

### **🔹 Educational Agent Template**
```json
{
  "id": "EducationTutorAgent",
  "name": "Education & Tutoring Agent",
  "description": "Provides educational support and tutoring assistance", 
  "capabilities": ["tutoring", "educational_support", "learning_guidance", "academic_help"],
  "keywords": ["education", "tutoring", "learning", "study", "academic", "school", "homework", "teaching"],
  "priority": 2,
  "system_prompt_template": "You are an educational specialist and tutor. Provide clear explanations, learning strategies, and academic guidance. Adapt your teaching style to help students understand complex concepts."
}
```

---

## 🛠️ **How to Add Your Agent**

### **Step-by-Step Instructions:**

1. **Open** `core/agents.json` in your text editor

2. **Find** the `"agents"` array (it's a list with `[` and `]`)

3. **Copy** one of the templates above

4. **Customize** the template:
   - Change `"id"` to your agent's unique name (no spaces)
   - Update `"name"` to the display name
   - Write a brief `"description"`
   - List your agent's `"capabilities"`
   - Add `"keywords"` that will trigger your agent
   - Write a `"system_prompt_template"` describing the agent's role

5. **Insert** your customized template into the agents array

6. **Save** the file

7. **Restart** your system

### **Example: Adding a Legal Agent**

Here's exactly what you'd add to the agents array:

```json
{
  "id": "LegalAdvisorAgent",
  "name": "Legal Advisory Agent",
  "description": "Provides legal information and guidance",
  "capabilities": ["legal_information", "contract_basics", "compliance_guidance", "legal_research"],
  "keywords": ["legal", "law", "contract", "compliance", "attorney", "lawsuit", "rights", "liability"],
  "priority": 2,
  "system_prompt_template": "You are a legal information specialist. Provide general legal information and guidance. Always emphasize that users should consult qualified attorneys for specific legal advice and that this is not a substitute for professional legal counsel."
}
```

---

## ⚙️ **Configuration Options Explained**

### **Required Fields:**
- **`id`**: Unique identifier (no spaces, use CamelCase)
- **`name`**: Human-readable display name
- **`description`**: Brief explanation of the agent's purpose
- **`keywords`**: Words that trigger this agent (array of strings)

### **Optional Fields:**
- **`capabilities`**: List of what the agent can do
- **`priority`**: 1=highest, 5=lowest (default: 3)
- **`system_prompt_template`**: Instructions for the AI model

### **Keywords Best Practices:**
- Use 5-10 relevant trigger words
- Include synonyms and related terms
- Think about how users would naturally ask questions
- Examples: For a fitness agent: `["fitness", "exercise", "workout", "gym", "health", "training"]`

---

## 🧪 **Testing Your New Agent**

### **Test Your Agent:**
1. Restart the system after saving `agents.json`
2. Ask a question using your agent's keywords
3. Verify the agent responds correctly
4. Check that the agent appears in multi-agent responses

### **Example Test Queries:**
- **Business Agent**: "I need business strategy advice for my startup"
- **Health Agent**: "What are some good fitness routines for beginners?"
- **Tech Agent**: "My computer is running slowly, how can I fix it?"
- **Legal Agent**: "What should I know about signing a contract?"

---

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **Agent Not Responding**
- Check that your keywords are in the query
- Ensure JSON syntax is correct (commas, quotes, brackets)
- Restart the system after changes

#### **Syntax Errors**
- Use a JSON validator online to check your syntax
- Make sure every `{` has a matching `}`
- Check for missing commas between items

#### **Agent Appears But Gives Generic Responses**
- Update the `system_prompt_template` to be more specific
- Add more detailed `capabilities`
- Use more descriptive keywords

### **JSON Validation:**
Use online tools like jsonlint.com to validate your JSON before saving.

---

## 🎨 **Advanced Customization**

### **Agent Personality:**
You can customize agent personality in the `system_prompt_template`:

```json
"system_prompt_template": "You are a friendly and enthusiastic fitness coach. Use motivational language, provide practical workout tips, and always encourage users to stay active. Include emojis in your responses to make them engaging."
```

### **Specialized Knowledge:**
Make agents domain experts:

```json
"system_prompt_template": "You are a certified financial advisor with expertise in personal finance, investment strategies, and retirement planning. Provide detailed, actionable financial advice while emphasizing the importance of individual financial situations."
```

---

## 📋 **Complete Example: Adding a Customer Service Agent**

Here's a complete example of adding a customer service agent:

### **1. Your Custom Agent:**
```json
{
  "id": "CustomerServiceAgent",
  "name": "Customer Service Specialist",
  "description": "Handles customer inquiries, support requests, and service issues",
  "capabilities": ["customer_support", "issue_resolution", "service_guidance", "complaint_handling"],
  "keywords": ["support", "help", "customer", "issue", "problem", "service", "complaint", "assistance"],
  "priority": 1,
  "system_prompt_template": "You are a professional customer service representative. Provide helpful, empathetic, and solution-focused responses to customer inquiries. Always maintain a positive, professional tone and offer clear steps to resolve issues."
}
```

### **2. Where to Add It:**
Open `core/agents.json` and add your agent to the `"agents"` array:

```json
{
  "entry_point": "RouterAgent",
  "version": "2.0.0", 
  "description": "JSON-Configurable LangGraph Multi-Agent System",
  "agents": [
    {
      "id": "RouterAgent",
      "name": "Query Router Agent",
      // ... existing router config
    },
    // ... other existing agents ...
    {
      "id": "CustomerServiceAgent",
      "name": "Customer Service Specialist", 
      "description": "Handles customer inquiries, support requests, and service issues",
      "capabilities": ["customer_support", "issue_resolution", "service_guidance", "complaint_handling"],
      "keywords": ["support", "help", "customer", "issue", "problem", "service", "complaint", "assistance"],
      "priority": 1,
      "system_prompt_template": "You are a professional customer service representative. Provide helpful, empathetic, and solution-focused responses to customer inquiries. Always maintain a positive, professional tone and offer clear steps to resolve issues."
    }
  ]
  // ... rest of config
}
```

### **3. Test Query:**
"I need help with a customer service issue"

---

## 🎉 **Success! You've Added a New Agent!**

Your new agent will now:
- ✅ Respond to queries containing its keywords
- ✅ Participate in multi-agent conversations
- ✅ Use its custom personality and expertise
- ✅ Appear in the system's agent list

**No programming required - just JSON configuration!**

---

## 📞 **Need Help?**

If you encounter issues:
1. Check JSON syntax with an online validator
2. Ensure all required fields are present  
3. Verify keywords are relevant to your use case
4. Restart the system after making changes

**Remember: This system is designed to be client-friendly - you don't need to be a programmer to add powerful new agents!** 🚀
