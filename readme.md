# Uber Eats Home Assistant Integration

This repository contains a Python script that integrates with the Uber Eats API to monitor the status of orders and update a Home Assistant sensor accordingly. The script is packaged as a Docker container for easy deployment and execution.

## Prerequisites

- Docker installed on your system
- Access to a Home Assistant instance with the necessary entities configured

## Home Assistant Requirements

To integrate with Home Assistant, you need to have the following entities configured:

- An [input text entity](https://www.home-assistant.io/integrations/input_text/) to hold the Uber Eats order URL.
- A custom template sensor to display the order status.

Here is an example configuration for the custom sensor:

```yaml
sensor:
  - platform: template
    sensors:
      uber_eats_order_status:
        friendly_name: "Uber Eats Order Status"
        value_template: "Unknown"
```

## Building the Docker Image

1. Clone this repository to your local machine.
2. Navigate to the cloned repository directory in your terminal.
3. Build the Docker image using the following command:

   ```sh
   docker build -t uber-eats-hassio .
   ```

## Running the Docker Container

To run the Docker container, execute the following command:

```sh
docker run -e API_SERVER_URL=my_api_server_url \
           -e ACCESS_TOKEN=my_access_token \
           -e SENSOR_ENTITY_ID=my_sensor_entity_id \
           -e URL_ENTITY_ID=my_url_entity_id \
           -e POLL_INTERVAL_SECONDS=60 \
           -e UBER_EATS_API_TIMEOUT_SECONDS=30 \
           uber-eats-hassio
```

Replace `my_api_server_url`, `my_access_token`, `my_sensor_entity_id`, and `my_url_entity_id` with the actual values for your environment variables.

## Configuration

The following environment variables are required to configure the integration:

- `API_SERVER_URL`: The URL of your Home Assistant API server (usually ends with `/api`).
- `ACCESS_TOKEN`: The long-lived access token for your Home Assistant API.
- `SENSOR_ENTITY_ID`: The entity ID of the Home Assistant sensor to update with the order status.
- `URL_ENTITY_ID`: The entity ID of the Home Assistant input text entity that holds the Uber Eats order URL.
- `POLL_INTERVAL_SECONDS`: The interval (in seconds) at which the script polls the Uber Eats API for order status updates.
- `UBER_EATS_API_TIMEOUT_SECONDS`: The timeout (in seconds) for requests to the Uber Eats API.

## Detailed Instructions for Using the Integration

To fully utilize the Uber Eats Home Assistant integration, follow these detailed instructions:

1. **Create an Input Text Entity**: In Home Assistant, create an [input text entity](https://www.home-assistant.io/integrations/input_text/) where you will store the Uber Eats order share URL. You can make the entity ID something like `input_text.uber_eats_order_url` (from the name: Uber Eats Order Url).

2. **Create a Custom Sensor**: Create a custom template sensor in Home Assistant to display the order status. See the [Home Assistant Requirements](#home-assistant-requirements) section for an example.

3. **Run the Docker Container**: Start the Docker container with the environment variables set for your Home Assistant instance. For more details on running the Docker container, see the [Running the Docker Container](#running-the-docker-container) section.

4. **Add the Order Share URL**: Once you place an order with Uber Eats, you will receive a share URL. Copy this URL and paste it into the input text entity you created in Home Assistant.
   You can use any other methods to edit this field, like a [Telegram integration](https://www.home-assistant.io/integrations/telegram_bot/#event-triggering), get creative 😎.

5. **Set Up Automations**: With the sensor now displaying the order status, you can create automations in Home Assistant based on the possible values such as "Preparing", "EnrouteToEater", "Delivered", and "Unknown". For example, you could notify yourself when the order is en route to you or send a message when the order has been delivered.

## Possible States of the Uber Eats `SENSOR_ENTITY_ID` Sensor

| State            | Meaning                                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------- |
| `Preparing`      | The restaurant is preparing the food for the order.                                         |
| `EnrouteToEater` | The delivery person has picked up the food and is on the way to deliver it to the customer. |
| `Delivered`      | The food has been successfully delivered to the customer.                                   |
| `Unknown`        | The status of the order cannot be determined.                                               |

## Deploying on your own Dockerhub

Many of us run our own Dockerhubs, these are my basic instructions, edit them for your hub:

```
docker build . --platform=linux/amd64 -t juandag/uber-eats-hassio
docker tag juandag/uber-eats-hassio:latest dockerhub.juandag.com/juandag/uber-eats-hassio:latest
docker push dockerhub.juandag.com/juandag/uber-eats-hassio:latest
```
