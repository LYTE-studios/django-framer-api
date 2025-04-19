#!/bin/sh

# Function to display help message
show_help() {
    echo "Blovio Development Script"
    echo
    echo "Usage: ./dev.sh [command]"
    echo
    echo "Commands:"
    echo "  up        Start the environment"
    echo "  down      Stop the environment"
    echo "  restart   Restart the environment"
    echo "  reload    Full rebuild and reload (for code changes)"
    echo "  logs      Show logs from all services"
    echo "  build     Rebuild all services"
    echo "  shell     Open a shell in the web container"
    echo "  test      Run tests"
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
        docker-compose up -d
        echo "Environment is starting..."
        echo "Access the application at http://localhost:8000"
        ;;
    down)
        check_docker_compose
        echo "Stopping environment..."
        docker-compose down
        ;;
    restart)
        check_docker_compose
        echo "Performing zero-downtime restart..."
        
        # Pull new images if any
        docker-compose pull

        # Start new containers alongside old ones
        docker-compose up -d --scale web=2 --no-recreate

        # Wait for new containers to be healthy
        echo "Waiting for new containers to be ready..."
        for i in $(seq 1 30); do
            if docker-compose ps | grep -q "healthy"; then
                break
            fi
            echo -n "."
            sleep 1
        done
        echo

        # Gracefully stop old containers
        docker-compose up -d --scale web=1 --no-recreate

        # Remove any orphaned containers
        docker-compose up -d --remove-orphans
        
        echo "Restart completed with zero downtime"
        ;;
    logs)
        check_docker_compose
        docker-compose logs -f
        ;;
    build)
        check_docker_compose
        echo "Rebuilding services..."
        docker-compose build --no-cache
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
    reload)
        check_docker_compose
        echo "Performing zero-downtime reload (for code changes)..."
        
        # Rebuild the web image in the background
        echo "Rebuilding web service..."
        docker-compose build web
        
        # Scale up with new image
        echo "Starting new containers..."
        docker-compose up -d --scale web=2 --no-recreate
        
        # Wait for new containers to be healthy
        echo "Waiting for new containers to be ready..."
        for i in $(seq 1 30); do
            if docker-compose ps | grep -q "healthy"; then
                break
            fi
            echo -n "."
            sleep 1
        done
        echo
        
        # Run migrations on the new container
        echo "Running migrations..."
        NEW_CONTAINER=$(docker-compose ps -q web | tail -n1)
        docker exec $NEW_CONTAINER python manage.py migrate
        
        # Scale down old containers
        echo "Removing old containers..."
        docker-compose up -d --scale web=1 --no-recreate
        
        # Remove any orphaned containers
        docker-compose up -d --remove-orphans
        
        echo "Reload completed with zero downtime! All changes are now live."
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