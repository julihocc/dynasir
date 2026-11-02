#!/bin/bash

# Epydemics Tutorial Management Script
# This script helps manage the epydemics-tutorial submodule easily

set -e

SUBMODULES=("epydemics-tutorial" "epydemics_global_model")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "This directory is not a git repository!"
        exit 1
    fi
}

# Function to initialize submodules
init_submodule() {
    print_header "Initializing submodules..."
    
    local all_initialized=true
    
    for submodule in "${SUBMODULES[@]}"; do
        if [ -d "$submodule" ] && [ "$(ls -A $submodule 2>/dev/null)" ]; then
            print_status "Submodule '$submodule' already initialized"
        else
            all_initialized=false
            break
        fi
    done
    
    if $all_initialized; then
        print_status "All submodules already initialized and populated"
    else
        print_status "Initializing and updating submodules..."
        git submodule update --init --recursive
        print_status "Submodules initialized successfully!"
    fi
}

# Function to update submodules to latest
update_submodule() {
    print_header "Updating submodules to latest version..."
    
    local missing_submodules=()
    for submodule in "${SUBMODULES[@]}"; do
        if [ ! -d "$submodule" ]; then
            missing_submodules+=("$submodule")
        fi
    done
    
    if [ ${#missing_submodules[@]} -gt 0 ]; then
        print_error "Submodules not found: ${missing_submodules[*]}. Run 'init' first."
        exit 1
    fi
    
    print_status "Fetching latest changes for all submodules..."
    git submodule update --remote --merge
    
    # Check if there are changes to commit
    local changes_detected=false
    for submodule in "${SUBMODULES[@]}"; do
        if ! git diff --quiet HEAD -- .gitmodules "$submodule"; then
            changes_detected=true
            break
        fi
    done
    
    if $changes_detected; then
        print_warning "Submodules have been updated. Consider committing the changes:"
        echo "  git add .gitmodules ${SUBMODULES[*]}"
        echo "  git commit -m \"Update submodules to latest version\""
    else
        print_status "All submodules are already up to date"
    fi
}

# Function to check submodules status
status_submodule() {
    print_header "Checking submodules status..."
    
    local missing_submodules=()
    local uninitialized_submodules=()
    
    for submodule in "${SUBMODULES[@]}"; do
        if [ ! -d "$submodule" ]; then
            missing_submodules+=("$submodule")
        elif [ ! -f "$submodule/.git" ] && [ ! -d "$submodule/.git" ]; then
            uninitialized_submodules+=("$submodule")
        fi
    done
    
    if [ ${#missing_submodules[@]} -gt 0 ]; then
        print_warning "Missing submodule directories: ${missing_submodules[*]}"
    fi
    
    if [ ${#uninitialized_submodules[@]} -gt 0 ]; then
        print_warning "Uninitialized submodules: ${uninitialized_submodules[*]}"
    fi
    
    print_status "Submodules status:"
    git submodule status
    
    # Check for uncommitted changes in main repo
    local main_repo_changes=false
    for submodule in "${SUBMODULES[@]}"; do
        if ! git diff --quiet HEAD -- .gitmodules "$submodule" 2>/dev/null; then
            main_repo_changes=true
            break
        fi
    done
    
    if $main_repo_changes; then
        print_warning "There are uncommitted changes related to submodules"
    fi
    
    # Check each submodule's local status
    for submodule in "${SUBMODULES[@]}"; do
        if [ -d "$submodule" ] && { [ -f "$submodule/.git" ] || [ -d "$submodule/.git" ]; }; then
            cd "$submodule"
            if ! git diff --quiet; then
                print_warning "Submodule '$submodule' has uncommitted changes"
            fi
            cd - > /dev/null
        fi
    done
}

# Function to reset submodules
reset_submodule() {
    print_header "Resetting submodules..."
    
    local existing_submodules=()
    for submodule in "${SUBMODULES[@]}"; do
        if [ -d "$submodule" ]; then
            existing_submodules+=("$submodule")
        fi
    done
    
    if [ ${#existing_submodules[@]} -eq 0 ]; then
        print_error "No submodules found"
        exit 1
    fi
    
    print_warning "This will reset all submodules to the committed state and lose any local changes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for submodule in "${existing_submodules[@]}"; do
            print_status "Resetting $submodule..."
            cd "$submodule"
            git reset --hard HEAD
            git clean -fd
            cd - > /dev/null
        done
        git submodule update --init --recursive
        print_status "All submodules reset successfully"
    else
        print_status "Reset cancelled"
    fi
}

# Function to open resources in default application
open_tutorial() {
    print_header "Opening resources..."
    
    local missing_submodules=()
    for submodule in "${SUBMODULES[@]}"; do
        if [ ! -d "$submodule" ]; then
            missing_submodules+=("$submodule")
        fi
    done
    
    if [ ${#missing_submodules[@]} -eq ${#SUBMODULES[@]} ]; then
        print_error "No submodules found. Run 'init' first."
        exit 1
    fi
    
    # Look for common files in each submodule
    for submodule in "${SUBMODULES[@]}"; do
        if [ -d "$submodule" ]; then
            print_status "Checking $submodule for resources..."
            
            RESOURCE_FILES=(
                "$submodule/README.md"
                "$submodule/tutorial.ipynb"
                "$submodule/global_model.ipynb"
                "$submodule/index.html"
                "$submodule/*.ipynb"
                "$submodule"
            )
            
            local found_file=false
            for file_pattern in "${RESOURCE_FILES[@]}"; do
                # Handle glob patterns
                if [[ "$file_pattern" == *"*"* ]]; then
                    for file in $file_pattern; do
                        if [ -e "$file" ]; then
                            print_status "Opening $file..."
                            if command -v code > /dev/null; then
                                code "$file"
                            elif command -v xdg-open > /dev/null; then
                                xdg-open "$file"
                            elif command -v open > /dev/null; then
                                open "$file"
                            else
                                print_status "Please open $file manually"
                            fi
                            found_file=true
                            break
                        fi
                    done
                else
                    if [ -e "$file_pattern" ]; then
                        print_status "Opening $file_pattern..."
                        if command -v code > /dev/null; then
                            code "$file_pattern"
                        elif command -v xdg-open > /dev/null; then
                            xdg-open "$file_pattern"
                        elif command -v open > /dev/null; then
                            open "$file_pattern"
                        else
                            print_status "Please open $file_pattern manually"
                        fi
                        found_file=true
                        break
                    fi
                fi
                
                if $found_file; then
                    break
                fi
            done
            
            if ! $found_file; then
                print_warning "No specific files found in $submodule. Opening directory..."
                if command -v code > /dev/null; then
                    code "$submodule"
                else
                    print_status "Please navigate to $submodule manually"
                fi
            fi
        fi
    done
}

# Function to show help
show_help() {
    cat << EOF
Epydemics Resources Management Script

USAGE:
    $0 <command>

COMMANDS:
    init        Initialize all submodules (tutorial and global model)
    update      Update all submodules to latest version
    status      Check status of all submodules
    reset       Reset all submodules to clean state (loses local changes!)
    open        Open resources in default application
    help        Show this help message

AVAILABLE RESOURCES:
    epydemics-tutorial       - Comprehensive tutorials and examples
    epydemics_global_model   - Complete global COVID-19 forecasting model

EXAMPLES:
    $0 init     # Initialize all submodules for first use
    $0 update   # Get latest content for all resources
    $0 status   # Check current state of all submodules
    $0 open     # Open available tutorial and model files

EOF
}

# Main script logic
main() {
    cd "$SCRIPT_DIR"
    check_git_repo
    
    case "${1:-help}" in
        "init")
            init_submodule
            ;;
        "update")
            update_submodule
            ;;
        "status")
            status_submodule
            ;;
        "reset")
            reset_submodule
            ;;
        "open")
            open_tutorial
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"