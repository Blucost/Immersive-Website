from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'sodium_pro_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ambience.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
    # Customization Persistence
    saved_video = db.Column(db.String(300), default='Apart_Rain_1.mp4')
    music_track = db.Column(db.String(300), default='')
    music_vol = db.Column(db.Float, default=0.5)
    ambience_track = db.Column(db.String(300), default='')
    ambience_vol = db.Column(db.Float, default=0.5)

    def get_settings(self):
        return {
            "video": self.saved_video,
            "music_track": self.music_track,
            "music_vol": self.music_vol,
            "ambience_track": self.ambience_track,
            "ambience_vol": self.ambience_vol
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Serve the Single Page Application
@app.route('/')
def index():
    # In production, index.html should be placed inside your templates/ folder 
    # or served directly from static depending on your setup.
    return app.send_static_file('index.html') if os.path.exists('static/index.html') else "Please place index.html in the static/ directory."

# --- JSON API Endpoints ---

@app.route('/api/user', methods=['GET'])
def get_user():
    if current_user.is_authenticated:
        return jsonify({"user": current_user.username, "settings": current_user.get_settings()})
    return jsonify({"user": None}), 401

@app.route('/sync', methods=['POST'])
@login_required
def sync_state():
    data = request.json
    if not data: return jsonify({"error": "No data"}), 400
    
    if 'video' in data: current_user.saved_video = data['video']
    if 'music_track' in data: current_user.music_track = data['music_track']
    if 'music_vol' in data: current_user.music_vol = float(data['music_vol'])
    if 'ambience_track' in data: current_user.ambience_track = data['ambience_track']
    if 'ambience_vol' in data: current_user.ambience_vol = float(data['ambience_vol'])
    
    db.session.commit()
    return jsonify({"status": "synced", "settings": current_user.get_settings()})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and user.password == data.get('password'):
        login_user(user)
        return jsonify({"status": "success", "user": user.username, "settings": user.get_settings()})
    return jsonify({"error": "Invalid credentials."}), 401

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists."}), 409
        
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({"status": "success", "user": user.username, "settings": user.get_settings()})

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"status": "logged_out"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Debug mode ensures auto-reloads on file changes
    app.run(debug=True, port=5000)