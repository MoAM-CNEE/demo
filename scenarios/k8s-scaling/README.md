``` 
TAG: front-end-latency
QUERY: sum(rate(request_duration_seconds_sum{name="front-end"}[1m])) * 1000 / sum(rate(request_duration_seconds_count{name="front-end"}[1m])) 
```
```
TAG: front-end-replicas-available
QUERY: kube_deployment_status_replicas_available{deployment="front-end", namespace="sock-shop"}
```
```
TAG: front-end-replicas-unavailable
QUERY: kube_deployment_status_replicas_unavailable{deployment="front-end", namespace="sock-shop"}
```