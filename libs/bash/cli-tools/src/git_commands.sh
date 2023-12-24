#!/bin/bash

function gup() {
    local message=$1
    if [[ -z "$message" ]]
    then
        echo "No commit message supplied, using default message"
        message="update" 
    fi
    git add .
    git commit -m "$message"
    git push
}

function gclone() {
    local name=$1
    if [[ -n $2 ]]
    then
        name=$2 
    fi
    git clone git@github.com:icarus612/"$1".git $name
}

function gsubclone() {
    local name=$1
    if [[ -n $2 ]]
    then
        name=$2 
    fi
    git submodule add git@github.com:icarus612/"$1".git $name
}