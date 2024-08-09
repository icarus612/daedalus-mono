#!/bin/bash

function gsf() {
	git submodule foreach $@
}

function gsfor() {
	if [[ $(git rev-parse --is-inside-work-tree) != true ]]; then
		return
	fi
	
	local sub_base=$(git rev-parse --show-toplevel)
	local current_dir=$(pwd)

	while getopts "l" flag; do
		case "${flag}" in
		l) sub_base=$current_dir ;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			return
			;;
		esac
	done
	
	shift $((OPTIND - 1))
	OPTIND=1

	find $sub_base -type f -name .git | while read line; do
		local location=$(dirname $line)
		local loc_base=$(basename $location)
		cd $location
		$@
	done
	cd $current_dir
}
