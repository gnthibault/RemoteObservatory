#!/bin/bash

DOCKER_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
MAIN_REPO_DIR="$DOCKER_DIR/.."
DOCKER_URL_REPO="gnthibault"
DOCKER_BASE_IMAGE="ubuntu:24.04"
DOCKER_ARM64_BASE_IMAGE="arm64v8/ubuntu:24.04"


docker_clean() {
    echo "-- DOCKER BUILD -- Now performs cleaning"

    # Now clean all exited containers
    echo "-- (Cleaning exited containers)"
    docker container prune --filter "until=24h" -f
    #for docker_hash in $(docker ps --quiet --filter=status=exited);
    #do
    #    docker rm -f $docker_hash
    #done

    # Now clean all dangling images
    echo "-- (Cleaning dangling image)"
    docker image prune -a --filter "until=4h" -f
    #for docker_hash in $(docker images --quiet --filter=unused=true);
    #do
    #    docker rmi -f $docker_hash
    #done

    # Now clean all dangling volume
    echo "-- (Cleaning associated ressources (volumes, network)"
    docker volume prune -f
    docker network prune --filter "until=24h" -f
    #for volume in $(docker volume ls -qf 'dangling=true');
    #do
    #    docker volume rm $volume
    #done
}

docker_tag() {
    #$1 is the image name
    #$2 is the actual tag
    echo "--docker tag $1:$2 $DOCKER_URL_REPO/$1:$2"
    docker tag $1:$2 $DOCKER_URL_REPO/$1:$2
    # For local kaniko please check https://github.com/GoogleContainerTools/kaniko?tab=readme-ov-file#running-kaniko-in-docker
    # kaniko --dockerfile=Dockerfile --context=/path/to/build/context --destination=my-registry.com/my-image:latest
}

docker_push() {
    #$1 is the image name
    #$2 is the actual tag
    echo "--docker push $DOCKER_URL_REPO/$1:$2"
    docker push $DOCKER_URL_REPO/$1:$2
    # For local kaniko please check https://github.com/GoogleContainerTools/kaniko?tab=readme-ov-file#running-kaniko-in-docker
    # kaniko --dockerfile=Dockerfile --context=/path/to/build/context --destination=my-registry.com/my-image:latest --push
}

docker_build () {
    #$1 the image name
    #$2 the directory where Dockerfile is located
    #$3 the tag
    #"$4": the docker build options, note the "" are importants
    IMAGE_NAME=$1:$3
    #remove leading and trailing double quote
    PARAMETERS=$(sed -e 's/^"//' -e 's/"$//' <<<"$4")
    PARAMETERS="$PARAMETERS --no-cache=true"
    echo "--docker build $PARAMETERS -t $IMAGE_NAME $2"
    # Use --progress=plain for debugging purpose
    docker build --progress=plain $PARAMETERS -t $IMAGE_NAME $2 # 2>&1 >/dev/null
    # For local kaniko please check https://github.com/GoogleContainerTools/kaniko?tab=readme-ov-file#running-kaniko-in-docker
    # kaniko --dockerfile=Dockerfile --context=/path/to/build/context --destination=my-image:latest --build-arg KEY=VALUE
    # you might want to use "--tar-path $APP_NAME.tar --no-push" and then use crane to push to remote
}

process_build() {
    #$1 the image name
    #$2 is the target ARCH parameter
    #$3 the (git) tag to be checked out and embedded in the image

    # define path and image name
    NAME=$1
    TAG=$2
    TARGET_ARCH=$3

    # Specify CPU/GPU related build parameters
    if [ TARGET_ARCH = "linux/arm64" ]
    then
        DOCKER_BASE_IMAGE=$DOCKER_ARM64_BASE_IMAGE
    else
        DOCKER_BASE_IMAGE=$DOCKER_BASE_IMAGE
    fi

    #Build a tar out of the code repo
    tar --directory $MAIN_REPO_DIR \
      -cvzf $DOCKER_DIR/code.tar.gz \
      --exclude "*.log"\
      --exclude "*.tar.gz" \
      --exclude "*.zip" \
      --exclude "*.pyc" .

    # Now build the actual production image
    echo "-- DOCKER BUILD -- Now building image"
    # Takes at input, the tag ($1) and directory ($2) whether it should embed
    # a copy of the codebase $3
    docker_build $NAME . $TAG \
        "\"--build-arg BASE_IMAGE=$DOCKER_BASE_IMAGE\
           --build-arg PYTHON_REQ=PYTHON_REQ_FILE\
           --platform $TARGET_ARCH\""

    # tag the freshly generated image
    # docker_tag $NAME $TAG
    # push the tagged image to the repo
    # docker_push $NAME $TAG

    echo "-- DOCKER BUILD -- Finished building image"
}

# Main script
if [[ -n "$1" ]]; then
   img_name="remote_observatory"
   image_tag=$1
else
    echo "Missing argument 1, please specify either a tag or latest"
    exit
fi

if [[ -n "$2" ]]; then
   target_arch=$2
else
    echo "Missing argument 2, please specify either linux/amd64 or linux/arm64"
    exit
fi

#Make sure the script fails if one non zero error code is returned
set -e

# Perform actual work
process_build $img_name $image_tag $target_arch