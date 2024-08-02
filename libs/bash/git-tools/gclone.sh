#!/bin/bash

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