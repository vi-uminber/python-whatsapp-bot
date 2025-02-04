import logging
import os

from app import create_app


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Flask app started")

    # Dynamically get the port from the environment variable or  default to 8000
    port = int(os.environ.get("PORT", 8000))

    # Run the app
    app.run(host="0.0.0.0", port=port, debug=True)
