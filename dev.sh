#!/bin/bash

# Function to display help message
show_help() {
    echo "LYTE Development Script"
    echo
    echo "Usage: ./dev.sh [command]"
    echo
    echo "Commands:"
    echo "  up        Start development environment"
    echo "  down      Stop development environment"
    echo "  restart   Restart development environment"
    echo "  logs      Show logs from all services"
    echo "  build     Rebuild all services"
    echo "  prod      Start production environment"
    echo "  shell     Open a shell in the web container"
    echo "  test      Run tests"
    echo "  reqs      Update requirements.txt from Pipfile"
    echo "  clean     Clean up unused Docker resources"
    echo "  help      Show this help message"
}

# Function to check if containers are running
is_running() {
    docker-compose -f docker-compose.dev.yaml ps --services --filter "status=running" | grep -q "web"
}

# Function to generate requirements
generate_requirements() {
    echo "Generating requirements.txt from Pipfile..."
    cd api && ./generate_requirements.sh
    cd ..
}

# Function to clean up Docker resources
cleanup_docker() {
    echo "Cleaning up Docker resources..."
    docker system prune -f
    echo "Cleanup complete!"
}

# Handle commands
case "$1" in
    up)
        echo "Starting development environment..."
        generate_requirements
        docker-compose -f docker-compose.dev.yaml up -d
        echo "Development environment is ready!"
        echo "Access the application at http://localhost:8000"
        ;;
    down)
        echo "Stopping development environment..."
        docker-compose -f docker-compose.dev.yaml down
        ;;
    restart)
        echo "Restarting development environment..."
        docker-compose -f docker-compose.dev.yaml down
        generate_requirements
        docker-compose -f docker-compose.dev.yaml up -d
        ;;
    logs)
        docker-compose -f docker-compose.dev.yaml logs -f
        ;;
    build)
        echo "Rebuilding services..."
        generate_requirements
        docker-compose -f docker-compose.dev.yaml build
        ;;
    prod)
        echo "Starting production environment..."
        generate_requirements
        docker-compose up -d
        ;;
    shell)
        if is_running; then
            docker-compose -f docker-compose.dev.yaml exec web /bin/bash
        else
            echo "Development environment is not running. Start it with './dev.sh up'"
        fi
        ;;
    test)
        if is_running; then
            docker-compose -f docker-compose.dev.yaml exec web python manage.py test
        else
            echo "Development environment is not running. Start it with './dev.sh up'"
        fi
        ;;
    reqs)
        generate_requirements
        ;;
    clean)
        cleanup_docker
        ;;
    help|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac