#!/bin/sh

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
    echo "  setup     Install required system dependencies"
    echo "  help      Show this help message"
}

# Function to check and install system dependencies
install_dependencies() {
    echo "Checking and installing required dependencies..."
    
    # Check if running as root
    if [ "$(id -u)" -ne 0 ]; then
        echo "Please run with sudo to install dependencies"
        exit 1
    fi

    # Update package list
    apt-get update

    # Install Python and pip if not installed
    if ! command -v python3 > /dev/null 2>&1; then
        echo "Installing Python..."
        apt-get install -y python3 python3-pip python3-venv
    fi

    # Install Docker if not installed
    if ! command -v docker > /dev/null 2>&1; then
        echo "Installing Docker..."
        apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        apt-get update
        apt-get install -y docker-ce
    fi

    # Install Docker Compose if not installed
    if ! command -v docker-compose > /dev/null 2>&1; then
        echo "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi

    # Start Docker service
    systemctl start docker
    systemctl enable docker

    # Add current user to docker group
    usermod -aG docker "$SUDO_USER"

    echo "All dependencies installed successfully!"
    echo "Please log out and back in for group changes to take effect."
}

# Function to check if containers are running
is_running() {
    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose -f docker-compose.dev.yaml ps --services --filter "status=running" | grep -q "web"
        return $?
    else
        echo "docker-compose not found"
        return 1
    fi
}

# Function to generate requirements
generate_requirements() {
    echo "Generating requirements.txt from Pipfile..."
    cd api
    if [ -f "generate_requirements.sh" ]; then
        chmod +x generate_requirements.sh
        ./generate_requirements.sh
    else
        echo "generate_requirements.sh not found!"
        exit 1
    fi
    cd ..
}

# Function to clean up Docker resources
cleanup_docker() {
    echo "Cleaning up Docker resources..."
    if command -v docker > /dev/null 2>&1; then
        docker system prune -f
        echo "Cleanup complete!"
    else
        echo "Docker not found"
        exit 1
    fi
}

# Check for docker-compose
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        echo "docker-compose not found. Please run 'sudo ./dev.sh setup' first"
        exit 1
    fi
}

# Handle commands
case "$1" in
    setup)
        install_dependencies
        ;;
    up)
        check_docker_compose
        echo "Starting development environment..."
        generate_requirements
        docker-compose -f docker-compose.dev.yaml up -d
        echo "Development environment is ready!"
        echo "Access the application at http://localhost:8000"
        ;;
    down)
        check_docker_compose
        echo "Stopping development environment..."
        docker-compose -f docker-compose.dev.yaml down
        ;;
    restart)
        check_docker_compose
        echo "Restarting development environment..."
        docker-compose -f docker-compose.dev.yaml down
        generate_requirements
        docker-compose -f docker-compose.dev.yaml up -d
        ;;
    logs)
        check_docker_compose
        docker-compose -f docker-compose.dev.yaml logs -f
        ;;
    build)
        check_docker_compose
        echo "Rebuilding services..."
        generate_requirements
        docker-compose -f docker-compose.dev.yaml build
        ;;
    prod)
        check_docker_compose
        echo "Starting production environment..."
        generate_requirements
        docker-compose up -d
        ;;
    shell)
        check_docker_compose
        if is_running; then
            docker-compose -f docker-compose.dev.yaml exec web /bin/bash
        else
            echo "Development environment is not running. Start it with './dev.sh up'"
        fi
        ;;
    test)
        check_docker_compose
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
        check_docker_compose
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