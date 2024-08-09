#!/bin/bash

is_subdirectory() {
    local file="$1"
    local dir="$2"

    local file_path=$(realpath "$file")
    local dir_path=$(realpath "$dir")

    if [[ "$file_path" == "$dir_path"* ]]; then
        return 0
    else
        return 1
    fi
}

check_all_subdirs() {
	local is_subdir=false
	local projects=("$@")
	for project in "${projects[@]}"; do
			if is_subdirectory "$file" "$project"; then
					is_subdir=true
					break
			fi
	done
	echo "$is_subdir"
}

# Function to create file tree
function find_readmes() {
		local base="$1"
		local to_search=()
		local projects=()
		for file in "$base"/*; do
				if [ -d "$file" ] && []; then
						to_search+=("$file")
				elif [[ "$(basename "$file")" == "README.md" ]]; then
						projects+=($(dirname "$file"))
				fi
		done
		echo "${files[@]}"
}

function create_tree() {
    local base="$1"
    local prefix="$2"
    local files=find_readmes "$base"
    local i=0
    local last=${#files[@]}

    for file in "${files[@]}"; do
        ((i++))
        if [ -d "$file" ]; then
            if [ $i -eq $last ]; then
                echo "${prefix}└── $(basename "$file")"
                create_tree "$file" "$prefix    "
            else
                echo "${prefix}├── $(basename "$file")"
                create_tree "$file" "$prefix│   "
            fi
        elif [[ "$(basename "$file")" == "README.md" ]]; then
            if [ $i -eq $last ]; then
                echo "${prefix}└── $(basename "$file") (Project Root)"
            else
                echo "${prefix}├── $(basename "$file") (Project Root)"
            fi
        fi
    done
}

# Start mapping from the current directory
echo "$(basename "$(pwd)")"
create_tree "." ""