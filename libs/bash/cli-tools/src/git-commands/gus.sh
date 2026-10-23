#!/bin/bash

function gus() {
	if [[ $(git rev-parse --is-inside-work-tree 2>/dev/null) != true ]]; then
		return
	fi

	local message="update"
	local branch=""
	local is_origin=false

	while getopts ":b:B:m:" flag; do
		case "${flag}" in
		b) branch=$OPTARG ;;
		B)
			branch=$OPTARG
			is_origin=true
			;;
		m) message=$OPTARG ;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			return
			;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=1

	git pull >/dev/null 2>&1
	git add --all
	git commit -m "$message"
	if [[ "$is_origin" = true ]]; then
		git push -u origin "$branch"
	elif [[ -n "$branch" ]]; then
		git push origin "$branch"
	else
		git push
	fi
}
