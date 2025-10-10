# Amrita UniBot - Enhanced Campus Assistant

An intelligent chatbot system for Amrita Vishwa Vidyapeetham with user authentication, conversation memory, and modern UI.

## 🌟 Features

### 🔐 User Authentication System
- **Secure Login/Signup**: Students can register using roll number and password
- **Password Hashing**: All passwords are securely hashed with salt
- **User Profiles**: Store student information (name, department, email)
- **Session Management**: Persistent login sessions

### 🧠 Conversation Memory (ChromaDB Integration)
- **Vector Database**: ChromaDB stores conversation embeddings for contextual understanding
- **Context-Aware Responses**: AI can reference previous conversations for better relevance
- **Conversation History**: Automatic saving and retrieval of chat history
- **Semantic Search**: Find relevant past conversations based on query meaning

### 🎨 Modern UI Design
- **Beautiful Interface**: Gradient backgrounds, chat bubbles, and smooth animations
- **Responsive Design**: Works perfectly on desktop and mobile
- **Amrita Branding**: Official university colors and logo
- **Interactive Elements**: Star ratings, smooth transitions, loading animations

### ⭐ Feedback System
- **Star Ratings**: 1-5 star rating system for conversations
- **Comments**: Optional text feedback from students
- **Analytics**: Track user satisfaction and improvement areas
- **Database Storage**: All feedback stored securely

### 🔧 Technical Enhancements
- **Error Handling**: Comprehensive error management and user feedback
- **Loading Animations**: Smooth loading states during API calls
- **OpenRouter Integration**: Maintains existing API structure
- **SQLite Database**: Lightweight, reliable data storage

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- OpenRouter API key
- Streamlit account (for deployment)

### Step 1: Clone and Setup
```bash
# Create project directory
mkdir amrita-chatbot-enhanced
cd amrita-chatbot-enhanced

# Copy all files to this directory
# Ensure you have: chatbot_enhanced.py, database.py, chroma_manager.py, requirements.txt
```

### Step 2: Install Dependencies
```bash
## 📦 Deployment (GitHub + Streamlit Cloud)

Follow these steps to publish the project to GitHub and deploy on Streamlit Cloud.

### 1) Initialize local git repo & first commit
Open a terminal in the project root and run:

```powershell
git init
git add --all
git commit -m "chore: initial commit - Amrita UniBot"
```

If you already have a repo, skip init and just add a remote and push.

### 2) Create a GitHub repository
- Go to https://github.com/new and create a new repo (public or private).
- Copy the remote URL and run:

```powershell
git remote add origin https://github.com/<your-username>/<your-repo>.git
git branch -M main
git push -u origin main
```

### 3) Prepare environment variables for Streamlit Cloud
- In your project root create a `.env` with:

```text
API_KEY=sk-or-v1-XXXXXXXXXXXX
```

Note: Streamlit Cloud doesn't read `.env` automatically. Set the API_KEY in Streamlit Cloud (app settings → Secrets) instead. Do NOT commit your `.env` file — it is already in `.gitignore`.

### 4) Confirm the Streamlit entrypoint
This repo provides `streamlit_app.py` which calls `chatbot_ver2.main()`; Streamlit Cloud will detect and run it.

### 5) Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io and log in with your GitHub account.
2. Click "New app" → choose the repository and branch (main) you pushed to.
3. For "Main file path" enter `streamlit_app.py` (or browse and select it).
4. Add the API key as a secret: Settings → Secrets → add `API_KEY` with your OpenRouter key.
5. Click Deploy.

### 6) Post-deploy notes
- If your app needs additional system-level packages or you see errors about missing wheels, check the Streamlit Cloud logs and adjust `requirements.txt` accordingly.
- If ChromaDB stores data locally, consider using external persistent storage or set up a dedicated vector DB for production.

pip install -r requirements.txt
```

### Step 3: Environment Configuration
Create a `.env` file in your project root:
```env
API_KEY=your_openrouter_api_key_here
```

### Step 4: Run the Application
```bash
streamlit run chatbot_enhanced.py
```

The application will automatically:
- Create SQLite database tables
- Initialize ChromaDB collections
- Set up authentication system

## 📁 Project Structure

```
amrita-chatbot-enhanced/
│
├── chatbot_enhanced.py    # Main application
├── database.py            # SQLite database management
├── chroma_manager.py      # ChromaDB integration
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # API key (create this)
│
├── amrita_chatbot.db     # SQLite database (auto-created)
└── chroma_db/           # ChromaDB data (auto-created)
```

## 🔐 Security Features

### Password Security
- **Salted Hashing**: Each password gets a unique salt
- **SHA-256 Algorithm**: Industry-standard hashing
- **Secure Storage**: Hash and salt stored separately

### Data Protection
- **User Isolation**: Each user can only access their own data
- **Session Management**: Secure session handling
- **Privacy Compliance**: Data deletion capabilities

### API Security
- **Key Validation**: Ensures proper API key format
- **Request Headers**: Secure API communication
- **Error Handling**: No sensitive data exposure

## 💬 Usage Guide

### For Students
1. **Sign Up**: Register with your roll number and details
2. **Login**: Use your credentials to access the chatbot
3. **Chat**: Ask questions about Amrita University
4. **History**: View past conversations in the sidebar
5. **Feedback**: Rate conversations to help improve the system

### For Administrators
1. **Monitor Usage**: Check database for user activity
2. **Feedback Analysis**: Review ratings and comments
3. **System Maintenance**: Update knowledge base as needed

## 🎯 Conversation Topics

The chatbot can help with:
- **Admissions**: Process, requirements, deadlines
- **Academics**: Courses, departments, curriculum
- **Campus Life**: Hostels, facilities, activities
- **Placements**: Companies, packages, preparation
- **Research**: Opportunities, labs, publications
- **General Info**: Contact details, location, history

## 🔧 Customization

### Adding New Knowledge
Update the `KNOWLEDGE_BASE` variable in `chatbot_enhanced.py` with new information about the university.

### UI Customization
Modify the CSS styles in the `chat_interface()` function to change colors, fonts, or layouts.

### Database Schema
Extend the database tables in `database.py` to add new features like user preferences or advanced analytics.

## 📊 Analytics & Monitoring

### User Statistics
- Total registered users
- Active conversations
- Feedback ratings
- Popular query topics

### Performance Metrics
- Response times
- API usage
- Error rates
- User engagement

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
- Ensure write permissions in the application directory
- Check if SQLite is properly installed

**API Key Issues**
- Verify the API key format (should start with 'sk-or-v1-')
- Check if the .env file is in the correct location

**ChromaDB Errors**
- Ensure sufficient disk space for vector storage
- Check Python version compatibility

**Streamlit Deployment**
- Use Streamlit Cloud or set up proper hosting
- Configure environment variables securely

## 🔮 Future Enhancements

### Planned Features
- **Multi-language Support**: Tamil and Hindi interfaces
- **Voice Integration**: Speech-to-text and text-to-speech
- **Mobile App**: Native iOS and Android applications
- **Advanced Analytics**: Detailed usage insights
- **Integration**: Connect with university systems

### Technical Improvements
- **Caching**: Redis for better performance
- **Load Balancing**: Handle multiple concurrent users
- **API Rate Limiting**: Prevent abuse and manage costs
- **Backup System**: Regular database backups

## 📞 Support

For technical support or questions:
- Check the troubleshooting section
- Review Streamlit documentation
- Consult OpenRouter API documentation
- Contact the development team

## 📄 License

This project is created for Amrita Vishwa Vidyapeetham. Please ensure compliance with university policies and data protection regulations.

---

**Built with ❤️ for Amrita University**