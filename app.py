from flask import Flask
from flask_jwt_extended import JWTManager
from auth import auth

app = Flask(__name__)

# Configure the app
app.config.from_object("config.Config")

# Initialize JWT
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth, url_prefix="/auth")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)