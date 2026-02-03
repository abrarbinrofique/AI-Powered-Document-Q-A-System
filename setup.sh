#!/bin/bash

echo "========================================="
echo "DDQ Agent Setup Script"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file and set DB_PASSWORD and FERNET_KEY"
    echo ""
    echo "Generate Fernet key with:"
    echo "  python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    echo ""
    exit 1
fi

echo "Starting Docker services..."
docker-compose up --build -d

echo ""
echo "Waiting for services to be healthy..."
sleep 10

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  Frontend:  http://localhost:3000"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  ChromaDB:  http://localhost:8001"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000"
echo "2. Enter your OpenAI API key when prompted"
echo "3. Create a project via API or use the default"
echo "4. Upload documents and start generating answers"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo ""
