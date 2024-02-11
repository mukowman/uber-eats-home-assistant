# -*- coding: utf-8 -*-
"""Queries an Uber Eats API and updates a Home Assitant Sensor."""

import os
import json
import re
import time
import logging

from dotenv import load_dotenv
from homeassistant_api import Client, State
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if available.
load_dotenv()

# Home Assistant configuration variables
API_SERVER_URL = os.getenv('API_SERVER_URL')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
SENSOR_ENTITY_ID = os.getenv('SENSOR_ENTITY_ID')
URL_ENTITY_ID = os.getenv('URL_ENTITY_ID')
# Polling interval for checking order status
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '60'))
# Uber Eats API Timeout
UBER_EATS_API_TIMEOUT_SECONDS = int(
    os.getenv('UBER_EATS_API_TIMEOUT_SECONDS', '30'))


def get_order_uuid(uber_eats_share_url: str) -> str:
    """Extract the UUID from an Uber Eats order share URL."""
    pattern = ("/orders/"
               "([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})"
               "(?![?])")
    match = re.search(pattern, uber_eats_share_url)

    if match:
        return match.group(1)
    else:
        raise ValueError("Failed to extract order UUID from the URL.")


def get_order_status_api(uber_eats_share_url: str) -> str:
    """Retrieve the status of a given Uber Eats order using its share link."""
    url = 'https://www.ubereats.com/_p/api/getActiveOrdersV1'
    headers = {
        'authority': 'www.ubereats.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.ubereats.com',
        'pragma': 'no-cache',
        'referer': uber_eats_share_url,
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X  10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 '
                       'Safari/537.36 Edg/121.0.0.0'),
        'x-csrf-token': 'x',
        'x-uber-client-gitref': '726018ef17263626429ea42bd0e77bf88ad6a5d7'
    }
    data = {
        'orderUuid': get_order_uuid(uber_eats_share_url),
        'timezone': 'America/Los_Angeles',
        'showAppUpsellIllustration': True
    }

    response = requests.post(url, headers=headers, data=json.dumps(
        data), timeout=UBER_EATS_API_TIMEOUT_SECONDS)

    if response.status_code != 200:
        raise ValueError(
            f"Request failed with status code {response.status_code}.")

    json_response = response.json()
    order_phase = json_response['data']['orders'][0]['orderInfo']['orderPhase']

    if order_phase == 'COMPLETED':
        return "Delivered"
    elif order_phase == 'ACTIVE':
        if "Heading your way" in response.text:
            # Sometimes Uber doesn't update the analytics field, so we search for this magic text.
            return "EnrouteToEater"
        return json_response['data']['orders'][0]['analytics']['data']['order_status']
    else:
        return "Unknown"


def update_home_assistant_sensor(client: Client, new_status: str) -> None:
    """Update a Home Assistant template sensor with the new status."""
    new_state = State(entity_id=SENSOR_ENTITY_ID, state=new_status)
    client.set_state(new_state)
    logger.info("Updated sensor with status: %s", new_status)


def get_home_assistant_order_url(client: Client) -> str:
    """Fetch the Uber Eats URL from a Home Assistant input text entity."""
    url_input_state = client.get_state(entity_id=URL_ENTITY_ID)
    return url_input_state.state


def clear_home_assistant_order_url_after_delivery(client: Client, order_status: str) -> None:
    """Clear the Home Assistant input text entity for the Uber Eats URL post-delivery."""
    if order_status == 'Delivered':
        new_state = State(entity_id=URL_ENTITY_ID, state="")
        client.set_state(new_state)
        logger.info("Cleared Uber Eats URL after delivery.")


def main():
    """
    Main entry point for the script. Continuously checks the status of Uber Eats
    orders and updates a Home Assistant sensor accordingly.

    This function initializes a continuous loop that fetches the current Uber
    Eats order URL from a Home Assistant input text entity, retrieves the order
    status via the Uber Eats API, updates the Home Assistant sensor with the
    latest status, and clears the order URL after confirming delivery.
    The loop repeats every POLL_INTERVAL_SECONDS seconds.
    """
    while True:
        with Client(API_SERVER_URL, ACCESS_TOKEN) as client:
            order_url = get_home_assistant_order_url(client)
            if order_url and order_url != "unknown":
                order_status = get_order_status_api(order_url)
                update_home_assistant_sensor(client, order_status)
                clear_home_assistant_order_url_after_delivery(
                    client, order_status)
            else:
                logger.info(
                    "No order URL found, sleeping for %s seconds", POLL_INTERVAL_SECONDS)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
