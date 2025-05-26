``` 
TAG: front-end-latency
QUERY: sum(rate(request_duration_seconds_sum{name="front-end"}[1m])) * 1000 / sum(rate(request_duration_seconds_count{name="front-end"}[1m])) 
```
```
TAG: user-latency
QUERY: sum(rate(request_duration_seconds_sum{name="user"}[1m])) * 1000 / sum(rate(request_duration_seconds_count{name="user"}[1m]))
```
