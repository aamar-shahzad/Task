# Task Manager Application

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

## Running the Application (Using Docker Compose)

Ensure you have Docker and Docker Compose installed on your system.

1. **Check Docker Installation**

```bash
docker --version
docker-compose --version
```

2. **Build and Start the Application**

```bash
# Build and start the frontend and backend services
docker-compose up --build
```

3. **Access the Application**

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger UI)**: [http://localhost:3001/docs](http://localhost:3001/docs)

4. **Stop the Application**

```bash
# Stop running containers
docker-compose down
```

## Running the Application (Without Docker)

If you prefer to run the application without Docker, follow the steps below.

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

# Set environment variables
cp .env.example .env

# Configure the .env file with your specific settings

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 3001
```

## Deployment

To deploy the application using Docker, follow these steps:

1. **Build Docker Images**

```bash
# From the project root directory
docker-compose build
```

2. **Run the Containers in Detached Mode**

```bash
# Start containers in the background
docker-compose up -d
```

3. **Check Logs (Optional)**

```bash
# View logs for backend or frontend
docker-compose logs backend
docker-compose logs frontend
```

4. **Stop and Remove Containers**

```bash
# Stop and remove containers
docker-compose down
```

## Environment Variables

Ensure that all necessary environment variables are configured in the `docker-compose.yml` file or `.env` file. Modify as needed.

Example `.env` file in the `backend` directory:

```env
PORT=3001
GEMINI_API_KEY=your-api-key
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

