source /opt/workshops/elastic-retry.sh
export $(curl http://kubernetes-vm:9000/env | xargs)

# ------------- STREAMS

echo "/api/streams/_enable"
curl -X POST "$KIBANA_URL/api/streams/_enable" \
    --header "kbn-xsrf: true" \
    --header 'x-elastic-internal-origin: Kibana' \
    --header "Authorization: ApiKey $ELASTICSEARCH_APIKEY"

echo "/internal/kibana/settings"
curl -X POST "$KIBANA_URL/internal/kibana/settings" \
    --header 'Content-Type: application/json' \
    --header "kbn-xsrf: true" \
    --header "Authorization: ApiKey $ELASTICSEARCH_APIKEY" \
    --header 'x-elastic-internal-origin: Kibana' \
    -d '{"changes":{"observability:streamsEnableSignificantEvents":true}}'

# ------------- DATAVIEWS

echo "Disable field caching"
disable_field_caching() {
    local http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$KIBANA_URL/internal/kibana/settings" \
    --header 'Content-Type: application/json' \
    --header "kbn-xsrf: true" \
    --header "Authorization: Basic $ELASTICSEARCH_AUTH_BASE64" \
    --header 'x-elastic-internal-origin: Kibana' \
    -d '{"changes":{"data_views:cache_max_age":0}}')

    if echo $http_status | grep -q '^2'; then
        echo "Disabled field caching: $http_status"
        return 0
    else
        echo "Failed to disable field caching. HTTP status: $http_status"
        return 1
    fi
}
retry_command_lin disable_field_caching

