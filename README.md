# Team Formation App - Clean Duplicate

This is a clean duplicate of the working `team-formation-app-gazi-2` Heroku application. This Flask web application implements 7 scientific team formation algorithms using Neo4j database integration.

## 🚀 Quick Deploy to Heroku

To deploy this duplicate to Heroku:

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit - duplicate of team-formation-app-gazi-2"

# Create new Heroku app
heroku create your-new-app-name

# Set environment variables
heroku config:set NEO4J_URI="neo4j+s://cc773764.databases.neo4j.io"
heroku config:set NEO4J_USER="neo4j" 
heroku config:set NEO4J_PASSWORD="z2rSb4ew9gxVlqlrFk8l_VZQcVhIzBwgnlder4nKv1A"

# Deploy
git push heroku main
```

## 📁 Project Structure

```
team-formation-app-clean-duplicate/
├── app/                    # Main application directory
│   ├── __init__.py        # Flask app factory
│   ├── config.py          # Configuration settings
│   ├── routes.py          # API endpoints
│   ├── team_formation.py  # Core team formation algorithms
│   ├── forms.py           # Flask forms
│   ├── data/              # Data files
│   ├── static/            # CSS, JS files
│   └── templates/         # HTML templates
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku process file
├── runtime.txt           # Python version
├── wsgi.py               # WSGI entry point
├── run.py                # Development server
└── .env                  # Environment variables
```

## 🎯 Features

### 7 Team Formation Algorithms:
- **ACET**: All-Connections-Equal Team Formation
- **CAT**: Co-Authorship Team Formation  
- **OAT**: Organizational Affiliation Team Formation
- **PRT**: Prioritized Relationship Team Formation
- **COT**: Cohesion-Optimized Team Formation
- **TAT**: Time-Aware Team Formation
- **CIT**: Citation-Optimized Team Formation

### API Endpoints:
- `GET /` - Home page
- `GET /api/health` - Health check
- `GET /api/algorithms` - List available algorithms
- `GET /api/keywords` - Get available keywords
- `POST /api/form-teams` - Form teams using selected algorithm
- `GET /api/test_connection` - Test Neo4j database connection

## 🔧 Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run locally:
```bash
python run.py
```

3. Visit: `http://localhost:5000`

## 📊 Database

Uses Neo4j AuraDB with AMİNER dataset containing:
- Authors with skills and collaborations
- Papers with keywords and citations
- Organizational relationships

## 🌐 Original Working App

This is a duplicate of: `https://team-formation-app-gazi-2.herokuapp.com`

---

*Ready to deploy as an exact duplicate of the working team formation application!*
