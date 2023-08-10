# Generic imports
import json
import logging
import requests

class IndiWebManagerClient():

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        if config is None:
            config = dict(
                module="IndiWebManagedClient",
                host="localhost",
                port="8624",
                profile_name=""
            )
        self.host = config["host"]
        self.port = config["port"]
        self.profile_name = config["profile_name"]

    def reset_server(self):
        status, profile = self.get_server_status()
        if status:
            self.stop_server()
        self.start_server()

    def get_server_status(self):
        """
        Reply: [{"status": "False"}, {"active_profile": ""}]
        :return: 
        """
        try:
            base_url = f"http://{self.host}:{self.port}"
            req = f"{base_url}/api/server/status"
            response = requests.get(req)
            self.logger.debug(f"get_server_status - url {req} - code {response.status_code} - response:{response.text}")
            assert response.status_code == 200
            server_status = json.loads(response.text)
        except json.JSONDecodeError as e:
            msg = f"Cannot properly parse server status from {response.text} : {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Cannot get server status: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)
        else:
            status = [stat["status"] for stat in server_status][0] == "True"
            profile = [stat["active_profile"] for stat in server_status][0]
            return status, profile

    def start_server(self):
        try:
            base_url = f"http://{self.host}:{self.port}"
            req = f"{base_url}/api/server/start/{self.profile_name}"
            response = requests.post(req)
            self.logger.debug(f"start_server - url {req} - code {response.status_code} - response:{response.text}")
            assert response.status_code == 200
        except Exception as e:
            msg = f"Cannot start server: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def stop_server(self):
        try:
            base_url = f"http://{self.host}:{self.port}"
            req = f"{base_url}/api/server/stop"
            response = requests.post(req)
            self.logger.debug(f"start_server - url {req} - code {response.status_code} - response:{response.text}")
            assert response.status_code == 200
        except Exception as e:
            msg = f"Cannot start server: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)
