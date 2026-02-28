from flask import Flask
from flask_cors import CORS
from routes.recommend import recommend_bp
from routes.upload import upload_bp  
from routes.tryon import tryon_bp

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Register blueprints
app.register_blueprint(recommend_bp, url_prefix="/recommend")
app.register_blueprint(upload_bp)  # no prefix → handled in @upload_bp.route("/upload")
app.register_blueprint(tryon_bp)

if __name__ == "__main__":
    app.run(
        debug=True,
        extra_files=[],
        exclude_patterns=[
            "*\\site-packages\\*",
            "*\\mediapipe\\*",
            "*\\flask\\*",
            "*\\werkzeug\\*",
        ]
    )
