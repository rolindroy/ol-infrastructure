#!/bin/bash

# This script requires prior authentication via target "odl-concourse"

# The following variables need to be set, and will be different between RC and production:
# GIT_CONFIG_ORG=<the github organization>
# GITHUB_DOMAIN=<the github domain>
# OCW_WWW_REPO=<the github repo for the ocw-www site>
# OCW_CONTENT_BUCKET_PREVIEW=<the S3 preview bucket>
# OCW_CONTENT_BUCKET_RELEASE=<the S3 release bucket>
# OCW_STUDIO_BASE_URL=<the ocw-studio base url>
# OCW_STUDIO_BUCKET=<The S3 bucket used by ocw-studio>
# OCW_STUDIO_SITE=<The ocw-www website name (ie slug) in studio>
# OCW_HUGO_PROJECTS_BRANCH=<'release-candidate' on RC, 'release' on production>

# The following need to be set via vault, per environment and pipeline group (preview, release):
# fastly-service-id
# fastly-api-token
# git-private-key


BRANCHES=("preview" "release")

for branch in "${BRANCHES[@]}"
do
  if [[ $branch == "preview" ]]
  then
    OCW_CONTENT_BUCKET=$OCW_CONTENT_BUCKET_PREVIEW
    VERSION="draft"
  elif [[ $branch == "release" ]]
  then
    OCW_CONTENT_BUCKET=$OCW_CONTENT_BUCKET_RELEASE
    VERSION="live"
  else
    echo "Invalid branch $1"
    exit 1
  fi

  yes | fly -t odl-concourse set-pipeline \
  -p $VERSION \
  --team=ocw \
  --config=pipelines/ocw/pipeline-ocw-www.yml \
  --instance-var site=$OCW_STUDIO_SITE \
  -v git-domain=$GITHUB_DOMAIN \
  -v github-org=$GIT_CONFIG_ORG \
  -v ocw-www-repo=$OCW_WWW_REPO \
  -v ocw-www-repo-branch=$branch \
  -v ocw-bucket=$OCW_CONTENT_BUCKET \
  -v ocw-hugo-projects-branch=$OCW_HUGO_PROJECTS_BRANCH \
  -v ocw-studio-url=$OCW_STUDIO_BASE_URL \
  -v ocw-studio-bucket=$OCW_STUDIO_BUCKET \
  -v ocw-www-site=$OCW_STUDIO_SITE
done