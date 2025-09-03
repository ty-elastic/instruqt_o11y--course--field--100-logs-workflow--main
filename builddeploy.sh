arch=linux/amd64
course=latest
service=all
local=true
variant=none
otel=false
namespace=trading
region=0

while getopts "s:a:l:v:o:n:r:" opt
do
   case "$opt" in
      s ) service="$OPTARG" ;;
      o ) otel="$OPTARG" ;;
      a ) arch="$OPTARG" ;;
      l ) local="$OPTARG" ;;
      v ) variant="$OPTARG" ;;
      n ) namespace="$OPTARG" ;;
      r ) region="$OPTARG" ;;
   esac
done

echo $local
if [ "$local" = "true" ]; then
   docker run -d -p 5093:5000 --restart=always --name registry registry:2
fi

echo $service

./build.sh -a $arch -c $course -s $service -l $local -v $variant -x true -y false -z false
./deploy.sh -c $course -s $service -l $local -v $variant -o $otel -n $namespace -r $region
