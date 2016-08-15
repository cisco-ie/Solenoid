import ems_grpc_pb2

from grpc.beta import implementations


class CiscoGRPCClient(object):
    def __init__(self, server, port, user, password, timeout=10):
        """This class creates grpc calls using python.

        :param username: Username for device login
        :param password: Password for device login
        :param server: The ip address for the device
        :param port: The port for the device
        :type password: str
        :type username: str
        :type server: str
        :type port: int
    """
        self._server = server
        self._port = port
        self._channel = implementations.insecure_channel(self._server, self._port)
        self._stub = ems_grpc_pb2.beta_create_gRPCConfigOper_stub(self._channel)
        self._timeout = int(timeout)
        self._metadata = [('username', user), ('password', password)]

    def __repr__(self):
        return '%s(Server = %s, Port = %s, User = %s, Password = %s, Timeout = %s)' % (
            self.__class__.__name__,
            self._server,
            self._port,
            self._metadata[0][1],
            self._metadata[1][1],
            self._timeout
        )

    def get(self, path):
        """Get grpc call
            :param data: JSON
            :type data: str
            :return: Return the response object
            :rtype: Response stream object
        """
        message = ems_grpc_pb2.ConfigGetArgs(yangpathjson=path)
        responses = self._stub.GetConfig(message, self._timeout, metadata=self._metadata)
        objects = ''
        for response in responses:
            objects += response.yangjson
        return objects

    def patch(self, yangjson):
        """Merge grpc call equivalent  of PATCH RESTconf call
            :param data: JSON
            :type data: str
            :return: Return the response object
            :rtype: Response object
        """
        message = ems_grpc_pb2.ConfigArgs(yangjson=yangjson)
        response = self._stub.MergeConfig(message, self._timeout, metadata=self._metadata)
        return response

    def delete(self, yangjson):
        """delete grpc call
            :param data: JSON
            :type data: str
            :return: Return the response object
            :rtype: Response object
        """
        message = ems_grpc_pb2.ConfigArgs(yangjson=yangjson)
        response = self._stub.DeleteConfig(message, self._timeout, metadata=self._metadata)
        return response

    def put(self, yangjson):
        """Replace grpc call equivalent of PUT in restconf
            :param data: JSON
            :type data: str
            :return: Return the response object
            :rtype: Response object
        """
        message = ems_grpc_pb2.ConfigArgs(yangjson=yangjson)
        response = self._stub.ReplaceConfig(message, self._timeout, metadata=self._metadata)
        return response
