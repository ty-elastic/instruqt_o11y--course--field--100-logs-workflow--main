arch=linux/amd64
course=latest
service=all
local=false
variant=none

build_service=true
build_collector=true
build_lib=true

while getopts "a:l:c:s:x:y:z:v:" opt
do
   case "$opt" in
      a ) arch="$OPTARG" ;;
      c ) course="$OPTARG" ;;
      s ) service="$OPTARG" ;;
      l ) local="$OPTARG" ;;
      x ) build_service="$OPTARG" ;;
      y ) build_collector="$OPTARG" ;;
      z ) build_lib="$OPTARG" ;;
      v ) variant="$OPTARG" ;;
   esac
done

repo=us-central1-docker.pkg.dev/elastic-sa/tbekiares
if [ "$local" = "true" ]; then
    docker run -d -p 5093:5000 --restart=always --name registry registry:2
fi

if [ "$build_service" = "true" ]; then
    cd ./src
    ./build.sh -r $repo -s $service -c $course -v $variant -a $arch
    cd ..
fi

if [ "$build_collector" = "true" ]; then
    cd ./collector
    ./build.sh -r $repo -c $course -v $variant -a $arch
    cd ..
fi

if [ "$build_lib" = "true" ]; then
    cd ./lib
    ./build.sh -r $repo -c $course -v $variant -a $arch
    cd ..
fi
