#### init
There are two types of nodes in the cluster. 
- static - Can't be scaled down, not managed by Crossplane. Otherwise there would be a risk of deleting the whole cluster.
- dynamic - Can be scaled down, managed by Crossplane. Initially there are no such nodes.

#### changed
- scale up - Substitute i in `scale-up-kubernetes-cluster.yaml` and apply it.
- scale down - FilterByQuery - select any resource with label `group: kube-worker-auto-scaled` and delete it.
