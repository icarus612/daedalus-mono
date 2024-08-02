#!/bin/bash

function lcount() {
	ls -1 $1 | wc -l
}

function bfor() {
	local location=""
	local is_cat=false
	local is_loc=false
	local items=""
	local commands="$2"

	while getopts "l:c:" flag; do
		case "${flag}" in
		l)
			is_loc=true
			loc="$OPTARG"
			;;
		c)
			is_cat=true
			loc="$OPTARG"
			;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			return
			;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=1

	if [[ $is_cat == true ]]; then
		items=$(cat $loc)
	elif [[ $is_loc == true ]]; then
		items=$(ls $loc)
	else
		items=$1
		shift
	fi
	$items | xargs -I {} exec "$@"
}
