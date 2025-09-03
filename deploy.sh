course=latest
service=all
local=false
variant=none
otel=false
namespace=trading
region=0

while getopts "l:c:s:v:o:n:r:" opt
do
   case "$opt" in
      c ) course="$OPTARG" ;;
      s ) service="$OPTARG" ;;
      l ) local="$OPTARG" ;;
      v ) variant="$OPTARG" ;;
      o ) otel="$OPTARG" ;;
      n ) namespace="$OPTARG" ;;
      r ) region="$OPTARG" ;;
   esac
done

repo=us-central1-docker.pkg.dev/elastic-sa/tbekiares
if [ "$local" = "true" ]; then
    repo=localhost:5093
fi

export COURSE=$course
export REPO=$repo
export NAMESPACE=$namespace
export REGION=$region

if [ "$otel" = "true" ]; then
    # ---------- COLLECTOR

    cd collector
    rm -rf values.yaml
    curl -o values.yaml https://raw.githubusercontent.com/elastic/elastic-agent/refs/tags/v9.0.3/deploy/helm/edot-collector/kube-stack/values.yaml
    if [ -d "_courses/$variant" ]; then
        echo $variant;
        patch < _courses/$variant/init.patch
        envsubst < values.yaml > values.yaml.tmp && mv values.yaml.tmp values.yaml
    fi
    helm upgrade --install opentelemetry-kube-stack open-telemetry/opentelemetry-kube-stack \
    --namespace opentelemetry-operator-system \
    --values 'values.yaml' \
    --version '0.6.3'
    
    kubectl -n opentelemetry-operator-system rollout restart deployment/opentelemetry-kube-stack-opentelemetry-operator 
    cd ..

    # ---------- OPERATOR

    cd operator
    if [ -d "_courses/$variant" ]; then
        echo "applying variant"
        envsubst < _courses/$variant/init.yaml | kubectl -n opentelemetry-operator-system apply -f -
    fi
    cd ..

    sleep 30
fi

envsubst < k8s/yaml/_namespace.yaml | kubectl apply -f -
kubectl label ns $namespace namespace-node-affinity=enabled

if [ "$service" != "none" ]; then
    for file in k8s/yaml/*.yaml; do
        current_service=$(basename "$file")
        current_service="${current_service%.*}"
        echo $current_service
        echo $service
        if [[ "$service" == "all" || "$service" == "$current_service" ]]; then
            echo "deploying..."
            if [ -f "k8s/yaml/_courses/$variant/$current_service.yaml" ]; then
                echo "applying variant"
                envsubst < k8s/yaml/_courses/$variant/$current_service.yaml | kubectl apply -f -
            else
                envsubst < k8s/yaml/$current_service.yaml | kubectl apply -f -
            fi
            kubectl -n $namespace rollout restart deployment/$current_service
        fi
    done
fi
