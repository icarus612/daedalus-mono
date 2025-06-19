#!/bin/bash

function penv() {
    local name=${1:-".venv"}
    
    # Check if directory doesn't exist
    if [ ! -d "$name" ]; then
        echo "Creating virtual environment: $name"
        python -m venv "$name" || { echo "Failed to create venv"; return 1; }
    fi
    
    # Check if activate script exists
    if [ -f "$name/bin/activate" ]; then
        source "$name/bin/activate"
        echo "Activated virtual environment: $name"
    else
        echo "Error: $name/bin/activate not found"
        return 1
    fi
}