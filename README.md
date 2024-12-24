# cloud-provider-mdns

A cloud provider to register services exposed by your cluster in Multicast DNS.

This is a proof of concept that it is possible to maintain human-readable names in Multicast DNS based on mere
declarations of such names in Kubernetes resources, pointing to the edge on which it exposes those resources. It is
intended to simplify local development, without the need of running a DNS server or manually hacking your hosts file.

Basically run this, watch it find resources, then type them into your browser.

Your Kubernetes cluster will have some form of traffic routing implementation to expose services to you. The typical
methods of doing that are:

* A service of type Loadbalancer  
  Such services may receive an IP address from your cloud provider or tools such as [cloud-provider-kind](https://github.com/kubernetes-sigs/cloud-provider-kind). Their result is an accessible IP address you can use to directly interact with the service to which that IP is assigned. If you wish to use some human-readable name then you must edit your hosts file or register that IP address in DNS. If the IP address changes you must do so again. While this tool could register that IP address for you in mDNS, it would have to do so by evaluating some label or annotation and it doesn't currently do this, so **this doesn't work yet**.
* An Ingress Controller at the edge and Ingress resources exposing individual apps  
  The Ingress controller will expose itself using some IP address which it usually obtains by exposing a service of type Loadbalancer itself. Individual apps then associate themselves with that Ingress controller via an Ingress resource that defines the FQDN they want to be reachable as. **This works more or less**.
* The new [Kubernetes Gateway API](https://gateway-api.sigs.k8s.io) at the endge and HTTPRoutes exposing individual apps  
  The Kubernetes Gateway API is an abstraction of Ingress (actually including the scenario and replacing the Ingress resource with its HTTP and GRPCRoutes). The FQDN individual apps are exposed with is defined in the HTTPRoute and GRPCRoutes analogue to the Ingress resource). **This works**.

## How to run this

1. One-time: Build and install as described in the "How to build this" section below. 
2. Start your Kubernetes cluster and make sure your Kubernetes configuration has it set as its current context
3. In a separate terminal, start this tool and keep it running. Hit Ctrl-C to stop it.

```shell
$ /path/to/virtualenv/bin/cloud-provider-mdns
```

> It is not necessary to activate the virtual environment you installed the script in.

4. Declare an Ingress or a HTTPRoute with a hostname that ends in '.local'
5. Watch the output of cloud-provider-mdns
6. Type the name into your browser

## How to build this

Clone this repository, create a Python virtualenv (you'll need Python >= 3.12), then build and install:

```shell
$ python3 -mvenv /path/to/virtualenv
$ . /path/to/virtualenv/bin/activate

(venv) $ pip install -r requirements.dev.txt -r requirements.txt
... many lines omitted

(venv) $ python3 -mbuild -n --wheel
... many lines omitted
Successfully built cloud_provider_mdns-0.0.0.dev0-py3-none-any.whl

(venv) $ pip3 install dist/cloud_provider_mdns-*.whl
... many lines omitted
```

It is best to install the script into the virtual environment. If you do not like that, you can deactivate the
virtual environment and install into whatever your Python considers the user installation directory. On Linux, that
directory is going to be `~/.local`. On MacOs it's `~/Library/Python/<Python Version>`. If you don't like that either,
you can permanently set the PYTHONUSERBASE environment variable to wherever things are to be installed. Current Python
is very picky about you installing outside a virtual environment, so you must specify the `--user` and 
`--break-system-packages` options to pip when doing that. 

## Issues & Limitations

* There is currently no testsuite
* This has been tested on a Mac, Docker, kind, Istio and the new Kubernetes Gateway API
* This has been tested on a Mac, Docker Desktop Kubernetes and an nginx Ingress Controller
* There is an unclean shut down of the watch client session when cancelling the watch task
* The new Kubernetes Gateway API is not part of the mainline Kubernetes client API. See below how to generate model classes for it
* Ingress controllers sometimes take quite a bit of time to reconfigure themselves. Ingresses without a controller assigned are ignored until the next update cycle

## Notes

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

### Watching custom resources using the native Kubernetes client

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

