# Web-Based Chat Interface for RAG-Enhanced Q&A System

A brief description of what this project does and who it's for.

This project is a Task Manager Pro with a frontend built in ReactJS and a backend using Python with FastAPI. It uses Gemini as the language model and does not utilize any vector databases. The backend has endpoints to support the frontend and uses fake employee data from an Excel sheet to answer user questions. The system handles two categories of questions: general-purpose questions and specific-purpose questions, such as performing arithmetic operations on the data source for correct answers.

## Installation

Instructions on how to install and set up the project.

### Clone the Repository

```bash
# Clone the repository
git clone https://github.com/aamar-shahzad/Task.git

# Navigate to the project directory
cd Task
```

### Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the app
npm run start
```

### Backend

```bash
# Navigate to the backend directory
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --port 3001
```

## Usage

Instructions on how to use the project.

### Frontend

```bash
# Run the frontend
npm run start
```

### Backend

```bash
# Run the backend
uvicorn app.main:app --port 3001
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

