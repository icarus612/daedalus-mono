#!/bin/bash

function penv() {
    local name=${1:-".venv"}
    shift # Remove first arg.

    # Check if directory doesn't exist
    if [ ! -d "$name" ]; then
        echo "Creating virtual environment: $name"
        python -m venv "$name" || {
            echo "Failed to create venv"
            return 1
        }
    fi

    # Check if activate script exists
    if [ -f "$name/bin/activate" ]; then
        source "$name/bin/activate"
        echo "Activated virtual environment: $name"
    else
        echo "Error: $name/bin/activate not found"
        return 1
    fi

    OPTIND=1
    while getopts "r:" flag "$@"; do
        case "${flag}" in
        r)
            local req_file=${OPTARG:-"requirements.txt"}
            pip install -r "$req_file"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            return 1
            ;;
        esac
    done
    shift $((OPTIND - 1))
}
