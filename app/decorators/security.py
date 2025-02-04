from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac


def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(current_app.config["APP_SECRET"], "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)


def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip signature check for GET requests (used in webhook verification)
        if request.method == "GET":
            return f(*args, **kwargs)

        signature = request.headers.get("X-Hub-Signature-256", "")[7:]
        if not signature:
            logging.error("No signature found in headers")
            return jsonify({"status": "error", "message": "No signature found"}), 403

        # Validate signature for POST requests
        if not validate_signature(request.get_data(), signature):
            logging.error("Invalid signature")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403

        return f(*args, **kwargs)

    return decorated_function
