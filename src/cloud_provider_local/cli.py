import sys
import typing
import asyncio

import kubernetes_asyncio as kubernetes
import k8s_gateway_api
import zeroconf
import zeroconf.asyncio

async def watch_httproute():
  w = kubernetes.watch.Watch()
  api = kubernetes.client.CustomObjectsApi()
  aiozc = zeroconf.asyncio.AsyncZeroconf(ip_version=zeroconf.IPVersion.V4Only)

  async for event in w.stream(api.list_cluster_custom_object, 'gateway.networking.k8s.io', 'v1', 'httproutes'):
    route = k8s_gateway_api.models.io_k8s_networking_gateway_v1_http_route.IoK8sNetworkingGatewayV1HTTPRoute.model_validate(event['object'])
    if len(route.spec.hostnames) > 1:
      print(f'Warning: Multiple hostnames in HTTPRoute {route.metadata.namespace}/{route.metadata.name} are not yet supported.')
    hostname = route.spec.hostnames[0]
    svc_fqdn = f'{hostname.replace(".local", "")}._http._tcp.local.'
    fqdn = f'{hostname}.local' if not hostname.endswith('.local') else hostname

    # Try to find the gateways this httproute is attached to
    ip_addresses = []
    for parent in route.status.parents:
      gtw_raw = await api.get_namespaced_custom_object('gateway.networking.k8s.io', 'v1', parent.parent_ref.namespace, 'gateways', parent.parent_ref.name)
      addresses = gtw_raw.get('status', {}).get('addresses', {})
      for address in addresses:
        ip_addresses.append(address.get('value'))
    if len(ip_addresses) > 1:
      print(f'Warning: Multiple ip addresses in gateways are not yet supported.')

    zc_service = zeroconf.asyncio.AsyncServiceInfo(
      '_http._tcp.local.',
      svc_fqdn,
      port=80,
      addresses=ip_addresses,
      server=fqdn)
    await aiozc.async_register_service(zc_service)
    print(f'[HTTPRoute] - {event["type"]} - {route.metadata.namespace}/{route.metadata.name} - {svc_fqdn} Server: {fqdn} IP: {ip_addresses[0]}')
  w.stop()

async def main() -> int:
  await kubernetes.config.load_kube_config()
  try:
    async with asyncio.TaskGroup() as tg:
      #watch_gtw_task = tg.create_task(watch_gtw())
      watch_httproute_task = tg.create_task(watch_httproute())
  except asyncio.CancelledError:
    print('Shutting down...')
  return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
