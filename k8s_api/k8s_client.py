#!/usr/bin/env python3
# _*_ coding: utf-8 _*_


from kubernetes import client
from kubernetes.client.rest import ApiException
from pprint import pprint
import urllib3


class KubernetesApi(object):
    def __init__(self, api_host, api_token):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.configuration = client.Configuration()
        self.configuration.host = api_host
        self.configuration.verify_ssl = False
        self.configuration.api_key = {"authorization": "Bearer " + api_token}

        self.api_instance = client.CoreV1Api(client.ApiClient(self.configuration))

    def list_nodes(self):
        node_list = {}
        try:
            api_response = self.api_instance.list_node()
            for node in api_response.items:
                node_list[node.metadata.name] = {
                    'name': node.metadata.name,
                    'status': node.status.conditions[-1].type if node.status.conditions[-1].status == 'True' else 'NotReady',
                    'is_schedule': 'False',
                    'type': 'server'
                }
            return node_list
        except ApiException as e:
            print("Exception when calling CoreV1Api->list_node: %s\n" % e)

    def detail_node(self, node_name):
        try:
            api_response = self.api_instance.read_node(node_name)
            node_info = {
                'ip': api_response.metadata.name,
                'is_schedule': 'False',
                'create_time': api_response.metadata.creation_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'label': api_response.metadata.labels,
                'annotations': api_response.metadata.annotations,
                'nodeInfo': api_response.status.node_info,
                'containers': []
            }
            return node_info
        except ApiException as e:
            print("Exception when calling CoreV1Api->list_node: %s\n" % e)

if __name__ == '__main__':
    host = 'https://47.115.79.189:6443'
    token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6Ik1rbzFMVnNIbW15THNvUnNuOWo5bWROUDdDOTBTZmhMS0Y4NzFMQnc4X0EifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJkYXNoYm9hcmQtYWRtaW4tdG9rZW4tOTZidGwiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGFzaGJvYXJkLWFkbWluIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiOGJiZTQ4MWMtZmVhOS00YTU3LTk5NzEtMDI0ZDA5OTc0YTE0Iiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmUtc3lzdGVtOmRhc2hib2FyZC1hZG1pbiJ9.L01nLKqUCpq0UY2W1xUmDIVfzjy71ZaKCih8RJHc5RzHPXByfzN_IhG7YPQebwDqcNR5dXDjQqfhVA86wn4DimkNbZitRduA7eOM_jMvciGQ6VPKyEB2MqBaHVs1bcrHlkHurr08L2x3hCTU4rTKjLb0UfF_lk1FlaojUHAjg1EVjLT0fon2ILLGc1KeEaZ-KKLih7XgoUb47sImD-x-8b8qQztDBJKb_s_Yl3uBy7QE8tLPyxBMjHZxv9H55QbyXGNxF0Nbd3L34WYKY21fPTBJUXkvryuHyxtHSztnilpby_8HKZhK2WhPoF2BDg_mIke4f2V_rQvzTqoXgjyzWQ'
    pprint(KubernetesApi(host, token).detail_node('192.168.1.101'))