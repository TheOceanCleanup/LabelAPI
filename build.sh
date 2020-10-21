#!/bin/bash -e

latest_tag=$(git describe --tags `git rev-list --tags --max-count=1` 2> /dev/null || true)

echo "Enter version number (major.minor.patch) (most recent tag: $latest_tag)"
read version

rx='^[0-9]+\.[0-9]+\.[0-9]+$'
if ! [[ $version =~ $rx ]]; then
 echo "Aborting: Invalid tag"
 exit
fi

if git rev-parse "$version" >/dev/null 2>&1 ; then
  echo "Aborting: Tag $version already exists"
  exit
fi

export GIT_COMMIT=`git log -1 --format=%h`
export GIT_BRANCH=`git rev-parse --abbrev-ref HEAD`

if [[ $(git diff --stat) != '' ]]; then
  export GIT_STATUS="dirty"
else
  export GIT_STATUS="clean"
fi

docker build -t label-storage --build-arg=GIT_COMMIT=$GIT_COMMIT --build-arg=GIT_BRANCH=${GIT_BRANCH}-${GIT_STATUS} --build-arg=VERSION=$version .

if [[ $GIT_STATUS == 'clean' ]]; then
  git tag -a $version -m "Tagged release $version"

  az login
  az acr login --name tocacr
  docker tag label-storage tocacr.azurecr.io/label-storage:$version
  docker push tocacr.azurecr.io/label-storage:$version

  git push --tags
  echo
  echo "Ok - tagged and pushed release $version ($GIT_BRANCH @ $GIT_COMMIT)"
else
  echo
  echo "Working directory is dirty, image will not be deployed to the ACR and tag will not be applied"
fi
