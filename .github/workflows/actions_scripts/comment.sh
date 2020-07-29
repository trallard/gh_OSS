#!/bin/sh

# Make a comment on the PR

# This env comes from the GH actions context 

if [[ -z "${GITHUB_TOKEN}" ]]; then
	echo "Found a GITHUB_TOKEN env variable."
	exit 1
fi

if [[ -z "${ISSUE_NUMBER}" ]]; then
	echo "Found ISSUE-NUMBER."
	exit 1
fi

if [ -z "$1" ]
  then
    echo "No MESSAGE argument supplied.  Usage: COMMENT.sh <message>"
    exit 1
fi

MESSAGE=$1

MESSAGE=$1

## Set Vars
URI=https://api.github.com
API_VERSION=v3
API_HEADER="Accept: application/vnd.github.${API_VERSION}+json"
AUTH_HEADER="Authorization: token ${GITHUB_TOKEN}"

# Create a comment with APIv3 
# POST /repos/:owner/:repo/issues/:issue_number/comments

curl -XPOST -sSL \
    -d "{\"body\": \"$MESSAGE\"}" \
    -H "${AUTH_HEADER}" \
    -H "${API_HEADER}" \
    "${URI}/repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments"