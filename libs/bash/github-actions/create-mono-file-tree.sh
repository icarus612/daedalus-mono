done
}

print_tree() {
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
                if [ $count -eq $total_dirs ]; then
                    echo "${prefix}└── ${dir_name}"
                else
                    echo "${prefix}├── ${dir_name}"
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

build_tree() {
    local base_dir="$1"
    echo "Project Structure:"
    echo "$(basename "$base_dir")"
    print_tree "$base_dir" "$base_dir" ""
}

# Start building the tree from the current directory
build_tree "$(pwd)"