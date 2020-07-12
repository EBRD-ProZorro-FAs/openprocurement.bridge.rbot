config = {
    "worker_type": "contracting",
    "client_inc_step_timeout": 0.1,
    "client_dec_step_timeout": 0.02,
    "drop_threshold_client_cookies": 2,
    "worker_sleep": 5,
    "retry_default_timeout": 3,
    "retries_count": 10,
    "queue_timeout": 3,
    "bulk_save_limit": 100,
    "bulk_save_interval": 3,
    "resources_api_token": "",
    "resources_api_version": "",
    "public_resources_api_server": "",
    "input_resources_api_server": "",
    "input_public_resources_api_server": "",
    "input_resource": "tenders",
    "output_resources_api_server": "",
    "output_public_resources_api_server": "",
    "output_resource": "tenders",
    "handler_rBot": {
        "resources_api_token": "",
        "output_resources_api_token": "",
        "resources_api_version": "",
        "input_resources_api_token": "",
        "input_resources_api_server": "",
        "input_public_resources_api_server": "",
        "input_resource": "tenders",
        "output_resources_api_server": "",
        "output_public_resources_api_server": "",
        "output_resource": "tenders",
        'webreneder_url': 'http://localhost:8080'
    }
}

CONFIG_MAPPING = {
    "input_resources_api_token": "resources_api_token",
    "output_resources_api_token": "resources_api_token",
    "resources_api_version": "resources_api_version",
    "input_resources_api_server": "resources_api_server",
    "input_public_resources_api_server": "public_resources_api_server",
    "input_resource": "resource",
    "output_resource": "resource",
    "output_resources_api_server": "resources_api_server",
    "output_public_resources_api_server": "public_resources_api_server"
}
