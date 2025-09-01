1. Run k8s-scaling.
2. Select the time range to the period of performing the scenario. Copy the data from `front-end latency` plot (Inspect -> Data -> Download CSV). Store the exported data in the results directory.
3. Run amocna-k8s-scaling.
4. The same as 2.
5. Adjust `experiments_time_offset`.
6. Document `Comparison` and `loadtest replicas` plots.

Metrics used:
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
