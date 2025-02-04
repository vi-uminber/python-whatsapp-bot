import logging
import json
from urllib.parse import unquote
from flask import Blueprint, request, jsonify, current_app, make_response
import os
from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

webhook_blueprint = Blueprint("webhook", __name__)


def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    body = request.get_json()
    # logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verification for WhatsApp
@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    """Handle GET requests for webhook verification"""
    logging.info("\n=== Webhook Verification Request ===")
    logging.info(f"Full URL: {request.url}")
    logging.info(f"Raw Args: {dict(request.args)}")
    
    # Get verification parameters
    mode = request.args.get("hub.mode", "")
    token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    
    # Log raw values
    logging.info("\nRaw Values:")
    logging.info(f"- Mode: '{mode}'")
    logging.info(f"- Token: '{token}'")
    logging.info(f"- Challenge: '{challenge}'")
    
    # Get environment token
    env_token = os.getenv("VERIFY_TOKEN", "")
    hardcoded_token = "test"
    
    logging.info("\nToken Comparison:")
    logging.info(f"- Token from request: '{token}'")
    logging.info(f"- Token from env: '{env_token}'")
    logging.info(f"- Hardcoded token: '{hardcoded_token}'")
    
    # Check both tokens
    if mode == "subscribe" and (token == env_token or token == hardcoded_token):
        logging.info("\nVerification successful!")
        logging.info(f"Returning challenge: {challenge}")
        return challenge
    
    # Log failure details
    logging.error("\nVerification Failed:")
    if mode != "subscribe":
        logging.error(f"- Mode mismatch: Expected 'subscribe', got '{mode}'")
    if token != env_token and token != hardcoded_token:
        logging.error(f"- Token '{token}' doesn't match env token '{env_token}' or hardcoded token '{hardcoded_token}'")
    
    return "Verification failed", 403

@webhook_blueprint.route("/webhook", methods=["POST"])
def webhook_post():
    """Handle POST requests sent by Meta to your webhook"""
    return "OK", 200

@webhook_blueprint.route("/")
def index():
    return "WhatsApp Bot Server is running!"
