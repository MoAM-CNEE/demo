# shellcheck disable=SC2046
echo "$(date +'%Y-%m-%d %T') start test"

curr=0
for ((i=1; i<=6; i++)); do
    ((curr++))
    echo "$(date +'%Y-%m-%d %T') Scaling loadtest to $curr"
    kubectl scale deploy load-test -n loadtest --replicas="$curr"


    sleep 180
done
sleep 240
echo scaling down
kubectl scale deploy load-test -n loadtest --replicas=0
sleep 60
echo "$(date +'%Y-%m-%d %T') test finished"
