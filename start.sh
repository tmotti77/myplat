#!/bin/bash

# 🚀 Hybrid RAG Platform - Quick Start Script
# This script helps you get the platform running quickly

set -e

echo "🚀 Starting Hybrid RAG Platform..."
echo "======================================"

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Copying from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_info "Please edit .env file and add your OpenAI API key before continuing."
            print_info "Required: OPENAI_API_KEY=\"sk-your-key-here\""
            read -p "Press Enter after you've updated .env file..."
        else
            print_error ".env.example file not found!"
            exit 1
        fi
    fi
    print_status ".env file exists"
}

# Check if OpenAI API key is configured
check_openai_key() {
    if ! grep -q "sk-" .env 2>/dev/null; then
        print_warning "OpenAI API key not configured in .env file"
        print_info "Please add: OPENAI_API_KEY=\"sk-your-actual-key-here\""
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "OpenAI API key configured"
    fi
}

# Function to start with simple setup
start_simple() {
    print_info "Starting Simple Setup (PostgreSQL + Backend only)..."
    docker-compose -f docker-compose.simple.yml up -d
}

# Function to start with standard setup  
start_standard() {
    print_info "Starting Standard Setup (PostgreSQL + Backend)..."
    docker-compose up -d
}

# Function to start with full setup
start_full() {
    print_info "Starting Full Setup (All services)..."
    docker-compose -f docker-compose.full.yml up -d
}

# Function to start minimal setup
start_minimal() {
    print_info "Starting Minimal Setup (PostgreSQL only)..."
    docker-compose -f docker-compose.minimal.yml up -d
}

# Function to check service health
check_health() {
    print_info "Checking service health..."
    sleep 10
    
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_status "Backend is healthy!"
        echo
        print_info "🎉 Platform is ready!"
        echo
        echo "📍 Access URLs:"
        echo "   Backend API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo "   Health Check: http://localhost:8000/health"
        echo
        echo "🔑 Default Login (after starting frontend):"
        echo "   Email: admin@example.com"
        echo "   Password: admin123!"
        echo
        echo "📱 Next Steps:"
        echo "   1. cd frontend"
        echo "   2. npm install --legacy-peer-deps"
        echo "   3. npm run dev"
        echo "   4. Open http://localhost:3000"
    else
        print_warning "Backend not responding yet. Check logs with: docker-compose logs backend"
    fi
}

# Function to show logs
show_logs() {
    echo
    print_info "Recent logs:"
    docker-compose logs --tail=20 backend
}

# Main menu
show_menu() {
    echo
    echo "Choose setup type:"
    echo "1) 🟢 Simple (Recommended) - PostgreSQL + Backend"
    echo "2) 🔵 Standard - Same as Simple (default docker-compose.yml)"  
    echo "3) 🟣 Full - All services (Redis, Qdrant, Elasticsearch, Monitoring)"
    echo "4) 🟡 Minimal - PostgreSQL only"
    echo "5) 📊 Show logs"
    echo "6) 🛑 Stop all services"
    echo "7) 🧹 Clean up (remove containers and volumes)"
    echo
    read -p "Enter your choice (1-7): " choice
}

# Stop services
stop_services() {
    print_info "Stopping all services..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
    docker-compose -f docker-compose.full.yml down 2>/dev/null || true
    docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true
    print_status "All services stopped"
}

# Clean up
cleanup() {
    print_warning "This will remove all containers and data volumes!"
    read -p "Are you sure? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        stop_services
        print_info "Removing volumes..."
        docker volume rm $(docker volume ls -q | grep rag) 2>/dev/null || true
        docker system prune -f
        print_status "Cleanup complete"
    fi
}

# Main execution
main() {
    # Always check prerequisites
    check_docker
    check_env
    check_openai_key
    
    # If arguments provided, use them
    if [ $# -gt 0 ]; then
        case $1 in
            simple)
                start_simple
                check_health
                ;;
            standard)
                start_standard
                check_health
                ;;
            full)
                start_full
                check_health
                ;;
            minimal)
                start_minimal
                check_health
                ;;
            stop)
                stop_services
                ;;
            clean)
                cleanup
                ;;
            logs)
                show_logs
                ;;
            *)
                echo "Usage: $0 {simple|standard|full|minimal|stop|clean|logs}"
                exit 1
                ;;
        esac
        return
    fi
    
    # Interactive menu
    while true; do
        show_menu
        case $choice in
            1)
                start_simple
                check_health
                break
                ;;
            2)
                start_standard
                check_health
                break
                ;;
            3)
                start_full
                check_health
                break
                ;;
            4)
                start_minimal
                check_health
                break
                ;;
            5)
                show_logs
                ;;
            6)
                stop_services
                break
                ;;
            7)
                cleanup
                break
                ;;
            *)
                print_error "Invalid option. Please choose 1-7."
                ;;
        esac
    done
}

# Run main function
main "$@"