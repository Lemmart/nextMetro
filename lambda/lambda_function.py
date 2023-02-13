# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import requests
import os
import ask_sdk_core.utils as ask_utils
from utils import get_time_left_str

import boto3
ddb = boto3.client("dynamodb")

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import AskForPermissionsConsentCard
from ask_sdk_model.services import ServiceException
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

from pathlib import Path
from dotenv import load_dotenv

# The SkillBuilder object acts as the entry point for your skill, routing all request and response payloads to the handlers.
sb = CustomSkillBuilder(api_client=DefaultApiClient())

from ask_sdk_model import Response, services

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Read environment variables
basepath = Path()
basedir = str(basepath.cwd())
envars = basepath.cwd() / '.env'
load_dotenv(".env")

DIRECTIONS_API_KEY = os.getenv('GOOGLE_DIRECTIONS_API_KEY')

# Sample text from https://github.com/alexa/alexa-skills-kit-sdk-for-python/blob/master/samples/GetDeviceAddress/lambda/py/lambda_function.py
WELCOME = ("Welcome to the Sample Device Address API Skill!  "
           "You can ask for the device address by saying what is my "
           "address.  What do you want to ask?")
WHAT_DO_YOU_WANT = "What do you want to ask?"
NOTIFY_MISSING_PERMISSIONS = ("Please enable Location permissions in "
                              "the Amazon Alexa app.")
NO_ADDRESS = ("It looks like you don't have an address set. "
              "You can set your address from the companion app.")
UNSUPPORTED_ADDRESS = "Sorry! That destination isn't currently supported."
ADDRESS_AVAILABLE = "Here is your full address: {}, {}, {}"
ERROR = "Uh Oh. Looks like something went wrong."
LOCATION_FAILURE = ("There was an error with the Device Address API. "
                    "Please try again.")
GOODBYE = "Bye! Thanks for using the Sample Device Address API Skill!"
UNHANDLED = "This skill doesn't support that. Please ask something else"
HELP = ("You can use this skill by asking something like: "
        "whats my address?")

permissions = ["read::alexa:device:all:address"]
# Location Consent permission to be shown on the card. More information
# can be checked at
# https://developer.amazon.com/docs/custom-skills/device-address-api.html#sample-response-with-permission-card


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # speak_output = "Welcome, you can say Hello or Help. Which would you like to try?"
        speak_output = "Where to?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure I caught that. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class GoToStationIntentHandler(AbstractRequestHandler):
    """Handler for Go to Stations Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GoToStationIntent")(handler_input)
        
    def handle(self, handler_input):
        # useful example application reference: https://github.com/alexa-samples/skill-sample-python-first-skill/blob/master/module-4/README.md
        # https://github.com/alexa/alexa-skills-kit-sdk-for-python/blob/master/samples/GetDeviceAddress/lambda/py/lambda_function.py
        
        req_envelope = handler_input.request_envelope
        response_builder = handler_input.response_builder
        service_client_fact = handler_input.service_client_factory
        
        slots = req_envelope.request.intent.slots
        resolutions_per_authority = slots['toStation'].resolutions.resolutions_per_authority[0]
        
        try:
            toStationSlot = resolutions_per_authority.values[0].value.name.lower()
        except Exception:
            # Reject unknown destinations
            response_builder.speak(UNSUPPORTED_ADDRESS)
            return response_builder.response
        
        # Test to see if we need to present a card requesting address permissions
        if not (req_envelope.context.system.user.permissions and
                req_envelope.context.system.user.permissions.consent_token):
            logger.error(f"Permissions consent card required for user to allow use of current address")
            response_builder.speak(NOTIFY_MISSING_PERMISSIONS)
            response_builder.set_card(
                AskForPermissionsConsentCard(permissions=permissions))
            return response_builder.response

        # Get device address
        curr_address = None
        try:
            device_id = req_envelope.context.system.device.device_id
            device_addr_client = service_client_fact.get_device_address_service()
            addr = device_addr_client.get_full_address(device_id)

            if addr.address_line1 is None and addr.state_or_region is None:
                return response_builder.speak(NO_ADDRESS)
            else:
                curr_address = "{}, {}, {}".format(addr.address_line1, addr.state_or_region, addr.postal_code)
            
            logger.info(f"Found user current address {curr_address}")
        except ServiceException as e:
            logger.error(f"Failed to find user current address due to ServiceException:", e)
            response_builder.speak(ERROR)
            return response_builder.response
        except Exception as e:
            logger.error(f"Failed to find user current address due to unknown exception:", e)
            raise e

        # Lookup Google place ID (https://developers.google.com/maps/documentation/places/web-service/place-id) for destination address in database
        place_id = None
        try:
            ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
            ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')
            
            dynamodb = boto3.resource('dynamodb', region_name=ddb_region)
            
            table = dynamodb.Table(ddb_table_name)
            response = table.get_item(
                Key={
                    'id': toStationSlot
                }
            )
            if 'Item' in response:
                place_id = response['Item']['placeId']
                logger.info(f"Found place id {place_id} for {toStationSlot}")
            else:
                logger.error(f"Failed to find a valid place ID for slot {toStationSlot}")
        except BaseException as e:
            logger.error("Failed to retrieve destination address with error:", e)
            return response_builder.speak(ERROR)
        
        # find directions via API between current address and station address
        # use Google directions API with the place ids of the start and end locations
        # link: https://developers.google.com/maps/documentation/directions
        payload={}
        headers = {}
        sanitized_addr = curr_address.replace(' ', '+')
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={sanitized_addr}&destination=place_id:{place_id}&mode=transit&transit_mode=rail&key={DIRECTIONS_API_KEY}"
        response = requests.request("GET", url, headers=headers, data=payload)
        
        if (response.status_code != 200):
            logger.error(f"Failed to retrieve directions between {sanitized_addr} and {toStationSlot} [place id: {place_id}]")
            return response_builder.speak(ERROR)
        
        # Process departure stations and times
        logger.info(f"Retrieved directions data between {curr_address} and {toStationSlot} [place id: {place_id}]")
        resp_json = response.json()
        stations_and_departure_times = []
        for route in resp_json['routes']:
            # potential for multiple routes (e.g. 3 metro lines all going to the same stop)
            for leg in route['legs']:
                for step in leg['steps']:
                    # isolate the transit stops so that we can reflect it along with the departure time back to the user
                    if step['travel_mode'] == 'TRANSIT' and step['transit_details']['line']['vehicle']['type'] == 'SUBWAY':
                        stations_and_departure_times.append({
                            'station': step['transit_details']['departure_stop']['name'],
                            'departure_time': step['transit_details']['departure_time']['text'],
                            'arrival_time': step['transit_details']['arrival_time']['text'],
                            'epoch_departure_time': step['transit_details']['departure_time']['value'],
                            'line': step['transit_details']['line']['name'],
                            'line_short_name': step['transit_details']['line']['short_name']
                        })

        logger.info(f"Found a total of {len(stations_and_departure_times)} stations to depart from.")
        # Sort stations_and_departure_times by departure time
        stations_and_departure_times.sort(key=lambda x: x['epoch_departure_time'])
        
        logger.info(f"Departure stations have been sorted: {stations_and_departure_times}")

        # Build response text with stations and departure times
        stringified = ""
        for obj in stations_and_departure_times:
            stringified += f" The {obj['line']} leaves from {obj['station']} in {get_time_left_str(obj['epoch_departure_time'])} at {obj['departure_time']} and arrives at {obj['arrival_time']}."
        
        logger.info(f"Departure stations have been stringified: {stringified}")
        
        # Add nice closing message
        if len(stations_and_departure_times) > 0:
            speak_output = " Great!" + stringified
        else:
            speak_output = "Sorry! I didn't find any available routes."
        
        return (
            response_builder
                .speak(speak_output)
                .response
        )


# Make sure any new handlers or interceptors you've defined are included below. 
# The order matters - they're processed top to bottom.

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GoToStationIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()