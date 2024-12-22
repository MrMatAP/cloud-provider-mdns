# cloud-provider-local

A cloud provider emulation for local Kubernetes development

## How to build this

### How to generate your own Kubernetes client.

The Kubernetes Gateway API is not yet part of the Kubernetes Python API distribution in version 31.0.0. 
That client API is generated using [openapi-generator](https://openapi-generator.tech).

```shell
$ brew install openapi-generator
$ mkdir ~/build/k8s-api
$ kubectl get --raw /openapi/v2 > ~/build/k8s-api/openapi.json
$ openapi-generator generate -i k8s-api.json -g python -o ~/build/k8s-api
```

Specifying /openapi/v2 in the kubectl get command above will fetch the entire OpenAPI definition of your cluster, with
every CRD installed on it. If you take a look at what comes back for /openapi/v2 (or v3), you'll notice that it is a
simple mapping between the CRD API and the URI that defines it. It is perfectly possible to just fetch the CRD-specific
URI and generate client code just for that.

### Watching custom resources using the Kubernetes client

The upstream Kubernetes client adds the watch and config package, which are not part of the client we generate using
the method above. Worse, there are quite a few incompatibilities. The Watch.stream method forces 
`_preload_content = False` in kwargs, which the newer generated (Pydantic) classes refuse to deserialise. It is also
annoying to distribute a custom distribution of the API that just happens in your own cluster that doesn't necessarily
exist in anyone elses. A better option is to accept that such resources are returned as dicts rather than being
deserialised by the official Kubernetes client. Here is how you watch for such custom resources. If you still have the
generated models then it is perfectly possible to cast the event object into such a model.

```python
import kubernetes           # Upstream, official Kubernetes client
import k8s_gateway_api      # Generated ourselves using the method above
kubernetes.config.load_kube_config()
api = kubernetes.client.CustomObjectsApi()
w = kubernetes.watch.Watch()
for event in w.stream(api.list_cluster_custom_object, 'gateway.networking.k8s.io', 'v1', 'gateways'):
  print(event)
  gtw = k8s_gateway_api.models.io_k8s_networking_gateway_v1_gateway.IoK8sNetworkingGatewayV1Gateway.model_validate(event['object'])
```
