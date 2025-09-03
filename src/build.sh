arch=linux/amd64
course=latest
repo=us-central1-docker.pkg.dev/elastic-sa/tbekiares
service=all
variant=none
while getopts "r:a:c:s:v:" opt
do
   case "$opt" in
      a ) arch="$OPTARG" ;;
      c ) course="$OPTARG" ;;
      r ) repo="$OPTARG" ;;
      s ) service="$OPTARG" ;;
      v ) variant="$OPTARG" ;;
   esac
done

for service_dir in ./*/; do
    echo $service_dir
    if [[ -d "$service_dir" ]]; then
        current_service=$(basename "$service_dir")
        if [[ "$service" == "all" || "$service" == "$current_service" ]]; then
            echo $service
            echo $course
            echo $variant
            docker buildx build --platform $arch --build-arg VARIANT=$variant --progress plain -t $repo/$current_service:$course --output "type=registry,name=$repo/$current_service:$course" $service_dir
        fi
    fi
done
