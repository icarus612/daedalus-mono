#!/bin/bash

function print_tree() {
    local base_dir="$1"
    local current_dir="$2"
    local prefix="$3"
    local dirs=($current_dir/*)
    local total_dirs=${#dirs[@]}
    local count=0

    for dir in "${dirs[@]}"; do
        ((count++))
        if [ -d "$dir" ]; then
            local dir_name=$(basename "$dir")
            if [[ -f "$dir/README.md" || -f "$dir/README.txt" || -f "$dir/README" ]]; then
                local path=$(realpath --relative-to="$base_dir" "$dir")
								if [ $count -eq $total_dirs ]; then
                    echo "${prefix}└── <a href=\"/${path}\">${dir_name}<\/a>"
                else
                    echo "${prefix}├── <a href=\"/${path}\">${dir_name}<\/a>"
                fi
            else
                local subdirs=($dir/*)
                if [ ${#subdirs[@]} -gt 0 ]; then
                    if [ $count -eq $total_dirs ]; then
                        echo "${prefix}└── ${dir_name}"
                        print_tree "$base_dir" "$dir" "${prefix}    "
                    else
                        echo "${prefix}├── ${dir_name}"
                        print_tree "$base_dir" "$dir" "${prefix}│   "
                    fi
                else
                    if [ $count -eq $total_dirs ]; then
                        echo "${prefix}└── ${dir_name}"
                    else
                        echo "${prefix}├── ${dir_name}"
                    fi
                fi
            fi
        fi
    done
}

function build_tree() {
    local base_dir="$1"
    echo "$(basename "$base_dir")  "
    print_tree "$base_dir" "$base_dir" ""
}

build_dir="$(pwd)"
if [ -n "$1" ]; then
		build_dir="$1"
fi

build_tree "$build_dir"