from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import requests
import os
import sys
from pymongo import MongoClient
from urllib.parse import urlencode
import secrets
from datetime import datetime
from functools import wraps
import json

# Add the parent directory to sys.path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import config, fallback to hardcoded values if import fails
try:
    from configuration.config import owners, ownersTable
except ImportError:
    print("Warning: Could not import config.py, using fallback values")
    owners = [1317342800941023242, 1236275658796171334]
    ownersTable = [1317342800941023242, 1236275658796171334]

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Environment variables
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://arrowsbritisharmy:cXgXOnuDac4RnAbP@cluster.muqrpfg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster")
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')

# MongoDB setup - with error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.bot_configs
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    client = None
    db = None

# Discord API URLs
DISCORD_API_BASE = 'https://discord.com/api/v10'
DISCORD_CDN_BASE = 'https://cdn.discordapp.com'

# Bot owners loaded from config.py
OWNERS = ownersTable

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_bot_info():
    """Get bot information from Discord API"""
    if not DISCORD_BOT_TOKEN:
        return None
    try:
        headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
        response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting bot info: {e}")
    return None

def get_user_guilds(access_token):
    """Get user's guilds from Discord API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{DISCORD_API_BASE}/users/@me/guilds', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_bot_guilds():
    """Get bot's guilds from Discord API"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    response = requests.get(f'{DISCORD_API_BASE}/users/@me/guilds', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_guild_info(guild_id):
    """Get guild information from Discord API"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    response = requests.get(f'{DISCORD_API_BASE}/guilds/{guild_id}', headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_guild_roles(guild_id):
    """Get guild roles from Discord API"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    response = requests.get(f'{DISCORD_API_BASE}/guilds/{guild_id}/roles', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_guild_channels(guild_id):
    """Get guild channels from Discord API"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    response = requests.get(f'{DISCORD_API_BASE}/guilds/{guild_id}/channels', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def user_can_manage_guild(user_id, guild_id, user_guilds):
    """Check if user can manage the guild (owner or administrator)"""
    if int(user_id) in OWNERS:
        return True
    
    for guild in user_guilds:
        if str(guild['id']) == str(guild_id):
            # Check if user is owner or has administrator permissions
            if guild.get('owner') or (guild.get('permissions', 0) & 0x8) == 0x8:
                return True
    return False

@app.route('/')
def index():
    try:
        bot_info = get_bot_info()
        return render_template('index.html', bot_info=bot_info)
    except Exception as e:
        print(f"Error in index route: {e}")
        return "Service starting up...", 200

@app.route('/login')
def login():
    if not DISCORD_CLIENT_ID:
        return "Discord OAuth not configured", 500
    
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify guilds'
    }
    discord_login_url = f'{DISCORD_API_BASE}/oauth2/authorize?' + urlencode(params)
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        flash('Authorization failed', 'error')
        return redirect(url_for('index'))
    
    # Exchange code for access token
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(f'{DISCORD_API_BASE}/oauth2/token', data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        
        # Get user info
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            session['user'] = user_data
            session['access_token'] = access_token
            return redirect(url_for('dashboard'))
    
    flash('Login failed', 'error')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_guilds = get_user_guilds(session['access_token'])
    bot_guilds = get_bot_guilds()
    bot_guild_ids = [str(guild['id']) for guild in bot_guilds]
    
    # Filter guilds where user can manage and bot is present
    manageable_guilds = []
    for guild in user_guilds:
        if (str(guild['id']) in bot_guild_ids and 
            user_can_manage_guild(session['user']['id'], guild['id'], user_guilds)):
            manageable_guilds.append(guild)
    
    bot_info = get_bot_info()
    return render_template('dashboard.html', 
                         guilds=manageable_guilds, 
                         user=session['user'],
                         bot_info=bot_info)

@app.route('/configure/<guild_id>')
@login_required
def configure_guild(guild_id):
    user_guilds = get_user_guilds(session['access_token'])
    
    if not user_can_manage_guild(session['user']['id'], guild_id, user_guilds):
        flash('You do not have permission to manage this server', 'error')
        return redirect(url_for('dashboard'))
    
    guild_info = get_guild_info(guild_id)
    if not guild_info:
        flash('Server not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Get current config from MongoDB
    config = db.guild_configs.find_one({'guild_id': guild_id}) or {}
    
    # Get guild roles and channels
    roles = get_guild_roles(guild_id)
    channels = get_guild_channels(guild_id)
    
    bot_info = get_bot_info()
    return render_template('configure.html', 
                         guild=guild_info, 
                         config=config,
                         roles=roles,
                         channels=channels,
                         user=session['user'],
                         bot_info=bot_info)

@app.route('/save_config/<guild_id>', methods=['POST'])
@login_required
def save_config(guild_id):
    user_guilds = get_user_guilds(session['access_token'])
    
    if not user_can_manage_guild(session['user']['id'], guild_id, user_guilds):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    if not db:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        config_data = request.json
        config_data['guild_id'] = guild_id
        config_data['updated_at'] = datetime.utcnow()
        config_data['updated_by'] = session['user']['id']
        
        # Update or insert config
        db.guild_configs.update_one(
            {'guild_id': guild_id},
            {'$set': config_data},
            upsert=True
        )
        
        return jsonify({'success': True, 'message': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/invite')
def invite():
    bot_info = get_bot_info()
    if bot_info:
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot_info['id']}&permissions=8&scope=bot%20applications.commands"
        return redirect(invite_url)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
