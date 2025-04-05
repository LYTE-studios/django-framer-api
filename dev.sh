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
        docker-compose ps --services --filter "status=running" | grep -q "web"
        return $?
    else
        echo "docker-compose not found"
        return 1
    fi
}

# Function to generate requirements
generate_requirements() {
    echo "Starting requirements generation..."
    echo "Current directory: $(pwd)"
    
    # Check if we're in the right directory structure
    if [ ! -d "api" ]; then
        echo "Error: 'api' directory not found"
        echo "Please run this script from the project root directory"
        exit 1
    fi
    
    # Navigate to api directory
    cd api || exit 1
    echo "Changed to api directory: $(pwd)"
    
    # Make generate_requirements.sh executable and check its existence
    if [ ! -f "generate_requirements.sh" ]; then
        echo "Error: generate_requirements.sh not found in $(pwd)"
        cd ..
        exit 1
    fi
    
    echo "Making generate_requirements.sh executable..."
    chmod +x generate_requirements.sh
    
    # Run the script
    echo "Running generate_requirements.sh..."
    if ! ./generate_requirements.sh; then
        echo "Error: Failed to generate requirements.txt"
        cd ..
        exit 1
    fi
    
    # Return to original directory
    cd ..
}

# Function to wait for services
wait_for_services() {
    echo "Waiting for services to be ready..."
    
    # Wait for up to 30 seconds
    for i in $(seq 1 30); do
        if docker-compose ps | grep -q "running"; then
            echo "Services are ready!"
            return 0
        fi
        echo "Waiting... ($i/30)"
        sleep 1
    done
    
    echo "Error: Services failed to start within 30 seconds"
    docker-compose logs
    return 1
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
        echo "Starting environment..."
        generate_requirements
        docker-compose up -d
        if wait_for_services; then
            echo "Environment is ready!"
            echo "Access the application at http://localhost:8000"
        else
            echo "Failed to start services. Check the logs above for details."
            exit 1
        fi
        ;;
    down)
        check_docker_compose
        echo "Stopping environment..."
        docker-compose down
        ;;
    restart)
        check_docker_compose
        echo "Restarting environment..."
        docker-compose down
        generate_requirements
        docker-compose up -d
        if wait_for_services; then
            echo "Environment restarted successfully!"
        else
            echo "Failed to restart services. Check the logs above for details."
            exit 1
        fi
        ;;
    logs)
        check_docker_compose
        docker-compose logs -f
        ;;
    build)
        check_docker_compose
        echo "Rebuilding services..."
        generate_requirements
        docker-compose build --no-cache
        ;;
    prod)
        check_docker_compose
        echo "Starting production environment..."
        generate_requirements
        docker-compose up -d
        if wait_for_services; then
            echo "Production environment is ready!"
        else
            echo "Failed to start services. Check the logs above for details."
            exit 1
        fi
        ;;
    shell)
        check_docker_compose
        if is_running; then
            docker-compose exec web /bin/bash
        else
            echo "Environment is not running. Start it with './dev.sh up'"
        fi
        ;;
    test)
        check_docker_compose
        if is_running; then
            docker-compose exec web python manage.py test
        else
            echo "Environment is not running. Start it with './dev.sh up'"
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