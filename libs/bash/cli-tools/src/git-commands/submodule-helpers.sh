#!/bin/bash

function gsinit() {
	git submodule update --init --recursive
	gsfor 'git checkout main'
}

function gclone() {
	local name=$1
	if [[ -n $2 ]]; then
		name=$2
	fi
	git clone git@github.com:icarus612/"$1".git $name
	cd $name
	gsinit &
	cd -
}

function gsclone() {
	local name=$1
	if [[ -n $2 ]]; then
		name=$2
	fi
	git submodule add git@github.com:icarus612/"$1".git $name
}

function gspull() {
	local branch="main"
	while getopts "b:if" flag; do
		case "${flag}" in
		b) branch=$OPTARG ;;
		i) git submodule update --init --recursive ;;
		f) git fetch --recurse-submodules ;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			exit 1
			;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=1
	gsfor 'git pull origin $branch'
	git pull

}
