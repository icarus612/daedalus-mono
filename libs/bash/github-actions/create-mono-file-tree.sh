#!/bin/bash

function generate_tree() {
    local dir="$1"
    local prefix="$2"

    # Get list of directories and README.md files, sorted alphabetically
    local items=($(ls -1p "$dir" | grep -E "/$|README\.md$" | sort))
    local num_items=${#items[@]}

    for ((i=0; i<num_items; i++)); do
        local item="${items[$i]}"
        local is_last=$([[ $i -eq $((num_items-1)) ]] && echo 1 || echo 0)
        
        if [[ "$item" == */ ]]; then
            # It's a directory
            local dirname="${item%/}"
            if [[ $is_last -eq 1 ]]; then
                echo "${prefix}└── $dirname"
                generate_tree "$dir/$dirname" "$prefix    " 1
            else
                echo "${prefix}├── $dirname"
                generate_tree "$dir/$dirname" "$prefix│   " 0
            fi
        elif [[ "$item" == "README.md" ]]; then
            # It's a README.md file
            local link=$(grep -m 1 "https://github.com" "$dir/$item" | sed -E 's/.*\((https:\/\/github.com[^)]+)\).*/\1/')
            local name=$(basename "$(dirname "$dir/$item")")
            if [[ -n "$link" ]]; then
                if [[ $is_last -eq 1 ]]; then
                    echo "${prefix}└── [$name]($link)"
                else
                    echo "${prefix}├── [$name]($link)"
                fi
            fi
        fi
    done
}

generate_tree $@