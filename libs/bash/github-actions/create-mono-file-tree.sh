#!/bin/bash

find_readme_dirs() {
    find "$1" -type d \( ! -regex '.*/\..*' \) | while read -r dir; do
        if [[ -f "$dir/README.md" || -f "$dir/README.txt" || -f "$dir/README" ]]; then
            echo "$dir"
        fi
    done
}

print_tree() {
    local base_dir="$1"
    local current_dir="$2"
    local prefix="$3"
    local dirs=($current_dir/*)

    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            local dir_name=$(basename "$dir")
            if [[ -f "$dir/README.md" || -f "$dir/README.txt" || -f "$dir/README" ]]; then
                echo "${prefix}${dir_name}"
            else
                local subdirs=($dir/*)
                if [ ${#subdirs[@]} -gt 0 ]; then
                    echo "${prefix}${dir_name}"
                    print_tree "$base_dir" "$dir" "    $prefix"
                fi
            fi
        fi
    done
}

build_tree() {
    local base_dir="$1"
    echo "Project Structure:"
    echo "$(basename "$base_dir")"
    print_tree "$base_dir" "$base_dir" "    "
}

# Start building the tree from the current directory
build_tree "$(pwd)"