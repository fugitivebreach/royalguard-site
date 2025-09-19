#!/usr/bin/env python3
"""Royal Guard Bot Dashboard - Main Application"""

print("=== STARTING MAIN APP ===")

def build_default_config_for_template():
    """Build default config dict for the dashboard without importing project code.

    The website must run standalone on Railway, so we avoid importing configuration.config.
    Defaults are empty; MongoDB values will populate real settings when present.
    """
    return {
        # Roles
        'support_role_id': '',
        'moderator_role_id': '',
        'administrator_role_id': '',
        'suspended_role_id': '',
        'verified_role_id': '',
        'nitro_role_id': '',
        # Channels
        'moderation_logs': '',
        'tickets_log_channel_id': '',
        'transfer_log_channel_id': '',
        'update_logs_channel_id': '',
        'BOT_LOGS_CHANNEL_ID': '',
        'AutoMuteLogs': '',
        'GIVEAWAYS_CHANNEL_ID': '',
        'tickets_category_id': '',
        # Tokens and misc
        'ROWIFI_API_TOKEN': '',
        'TRELLO_API_KEY': '',
        'TRELLO_API_TOKEN': '',
        'SSU_GAME_LINK': '',
        # Grouping
        'main_group_id': '',
        'blacklisted_groups': [],
        'whitelisted_groups': [],
        'blacklisted_names': [],
        'groups_to_check': [],
        'colour_roles': [],
        'timezone_roles': [],
        # Additional fields
        'unfairMuteCategoryID': '',
        'watchlistRoleID': '',
        'developer_role_id_diff': '',
        'sib_role_id_diff': '',
        'cos_role_id_diff': '',
    }
print("=== IMPORTING MODULES ===")
try:
    from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
    print("✓ Flask imported")
    import requests
    print("✓ requests imported")
    import os
    import sys
    from pymongo import MongoClient
    print("✓ pymongo imported")
    from urllib.parse import urlencode
    import secrets
    from datetime import datetime
    from functools import wraps
    import json
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import error: {e}")
    raise

# Add the parent directory to sys.path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env files if available
try:
    from dotenv import load_dotenv  # type: ignore
    # Load .env from website/ first, then project root .env as fallback/override
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except Exception:
    # Fallback: simple loader for key=value lines if python-dotenv is not installed
    def _simple_load_env(env_path: str):
        try:
            if not os.path.exists(env_path):
                return
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)
        except Exception:
            pass
    _simple_load_env(os.path.join(os.path.dirname(__file__), '.env'))
    _simple_load_env(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Do not import any project python modules; only use environment and MongoDB
owners = [int(x) for x in os.getenv('OWNERS', '1317342800941023242').split(',') if x.strip().isdigit()]
ownersTable = owners[:]

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Environment variables
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
# Default redirect updated per user request; can still be overridden by environment
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://royalguard.up.railway.app/callback')

# Debug environment variables immediately
print("=== Flask App Startup Debug ===")
print(f"DISCORD_CLIENT_ID: {'SET' if DISCORD_CLIENT_ID else 'MISSING'}")
print(f"DISCORD_CLIENT_SECRET: {'SET' if DISCORD_CLIENT_SECRET else 'MISSING'}")  
print(f"DISCORD_BOT_TOKEN: {'SET' if DISCORD_BOT_TOKEN else 'MISSING'}")
print(f"MONGO_URI: {'SET' if MONGO_URI else 'MISSING'}")
print(f"REDIRECT_URI: {REDIRECT_URI}")
print("=== Environment Check Complete ===")

# MongoDB setup - with error handling
try:
    if MONGO_URI:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.bot_configs
        # Test connection
        client.admin.command('ping')
        print("MongoDB connection successful")
    else:
        print("MongoDB URI not configured")
        client = None
        db = None
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

def get_effective_redirect_uri() -> str:
    """Resolve the redirect URI dynamically based on the request environment.
    Priority:
      1) Explicit REDIRECT_URI env var
      2) Build from request headers (X-Forwarded-Proto/Host) -> https://host/callback
      3) Fallback to request.url_root + 'callback'
    """
    if REDIRECT_URI and REDIRECT_URI != 'http://localhost:5000/callback':
        return REDIRECT_URI
    try:
        # Respect proxy headers set by Railway/Load balancers
        proto = request.headers.get('X-Forwarded-Proto', request.scheme or 'https')
        host = request.headers.get('X-Forwarded-Host') or request.headers.get('Host')
        if host:
            return f"{proto}://{host}/callback"
        # Fallback to url_root
        root = request.url_root.rstrip('/')
        return f"{root}/callback"
    except Exception:
        return REDIRECT_URI

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
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{DISCORD_API_BASE}/users/@me/guilds', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get user guilds: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting user guilds: {e}")
        return []

def get_bot_guilds():
    """Get bot's guilds from Discord API"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    response = requests.get(f'{DISCORD_API_BASE}/users/@me/guilds', headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    return []

def get_guild_info(guild_id):
    """Get guild information from Discord API"""
    if not DISCORD_BOT_TOKEN:
        return None
    try:
        headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
        response = requests.get(f'{DISCORD_API_BASE}/guilds/{guild_id}', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get guild info for {guild_id}: {response.status_code}")
    except Exception as e:
        print(f"Error getting guild info: {e}")
    return None

def get_guild_roles(guild_id):
    """Get guild roles from Discord API"""
    if not DISCORD_BOT_TOKEN:
        return []
    try:
        headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
        response = requests.get(f'{DISCORD_API_BASE}/guilds/{guild_id}/roles', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get roles for guild {guild_id}: {response.status_code}")
    except Exception as e:
        print(f"Error getting guild roles: {e}")
    return []

def get_guild_channels(guild_id):
    """Get guild channels from Discord API"""
    if not DISCORD_BOT_TOKEN:
        return []
    try:
        headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
        response = requests.get(f'{DISCORD_API_BASE}/guilds/{guild_id}/channels', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get channels for guild {guild_id}: {response.status_code}")
    except Exception as e:
        print(f"Error getting guild channels: {e}")
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
        if not bot_info:
            bot_info = {'username': 'Royal Guard Bot', 'id': '1367420411922354196', 'avatar': None}
        return render_template('index.html', bot_info=bot_info)
    except Exception as e:
        print(f"Error in index route: {e}")
        # Return simple HTML that doesn't require templates
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Royal Guard Bot</title></head>
        <body>
            <h1>Royal Guard Bot Dashboard</h1>
            <p>Service is starting up...</p>
            <a href="/login">Login with Discord</a>
        </body>
        </html>
        """, 200

@app.route('/login')
def login():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        return "Discord OAuth not configured - missing client credentials", 500
    
    effective_redirect = get_effective_redirect_uri()
    try:
        print(f"OAuth: using redirect_uri={effective_redirect}")
    except Exception:
        pass

    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': effective_redirect,
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
    effective_redirect = get_effective_redirect_uri()
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': effective_redirect
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
    
    try:
        print(f"OAuth token exchange failed: status={response.status_code} body={response.text}")
        print(f"Using redirect_uri={effective_redirect}; ensure it exactly matches one of the Redirect URIs in your Discord application settings.")
    except Exception:
        pass

    flash('Login failed. Ensure your Discord application includes this exact redirect URI and your env vars are set.', 'error')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user_guilds = get_user_guilds(session['access_token']) or []
        bot_guilds = get_bot_guilds() or []
        bot_guild_ids = [str(guild['id']) for guild in bot_guilds]
        
        # Filter guilds where user can manage and bot is present
        manageable_guilds = []
        for guild in user_guilds:
            if (str(guild['id']) in bot_guild_ids and 
                user_can_manage_guild(session['user']['id'], guild['id'], user_guilds)):
                manageable_guilds.append(guild)
        
        # Add fallback guild if no guilds found
        if not manageable_guilds:
            manageable_guilds = [{
                'id': '1371945471207018497',
                'name': 'Royal Guard Server',
                'icon': None
            }]
        
        bot_info = get_bot_info() or {'username': 'Royal Guard Bot', 'id': '1367420411922354196'}
        return render_template('dashboard.html', 
                             guilds=manageable_guilds, 
                             user=session['user'],
                             bot_info=bot_info)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return f"<h1>Dashboard</h1><p>Welcome {session['user']['username']}</p><a href='/configure/1371945471207018497'>Configure Server</a>", 200

@app.route('/configure/<guild_id>')
@login_required
def configure_guild(guild_id):
    try:
        # Get guild info from Discord API or use fallback
        guild_info = get_guild_info(guild_id) or {
            'id': guild_id,
            'name': f'Server {guild_id}',
            'icon': None
        }
        
        # Load configuration from database
        if db is not None:
            try:
                print(f"Looking for config with guild_id: '{str(guild_id)}'")
                config = db.guild_configs.find_one({'guild_id': str(guild_id)}) or {}
                print(f"Config loaded from DB: {len(config)} keys")
                if config:
                    print(f"Config keys: {list(config.keys())[:10]}")  # Show first 10 keys
                else:
                    print("No config found in database")
                    # Check if there are any configs at all
                    total_configs = db.guild_configs.count_documents({})
                    print(f"Total configs in database: {total_configs}")
                    if total_configs > 0:
                        sample_config = db.guild_configs.find_one({})
                        print(f"Sample config guild_id: '{sample_config.get('guild_id')}' (type: {type(sample_config.get('guild_id'))})")
            except Exception as e:
                print(f"MongoDB error: {e}")
                config = {}
        else:
            print("No database connection, using empty config")
            config = {}
        
        # Merge with defaults so configure.html always has expected keys
        defaults = build_default_config_for_template()
        # Precedence: DB > defaults (no project imports on Railway)
        merged_config = {**defaults, **config}
        
        # Coerce specific fields to int to match template comparisons that use raw role.id (no |string)
        def coerce_int_field(cfg, key):
            val = cfg.get(key)
            try:
                if isinstance(val, str) and val.isdigit():
                    cfg[key] = int(val)
                elif isinstance(val, (int, float)):
                    cfg[key] = int(val)
            except Exception:
                pass
        
        # Coerce all role and channel fields to integers
        role_fields = [
            # Basic roles
            'support_role_id', 'moderator_role_id', 'administrator_role_id', 
            'suspended_role_id', 'verified_role_id', 'nitro_role_id',
            # Verification roles
            'chiefsofstaff_role_id', 'op_role_id',
            # Ticket roles
            'support_team_role_id', 'moderator_role_id_diff', 'administrator_role_id_diff',
            'developer_role_id_diff', 'sib_role_id_diff', 'cos_role_id_diff',
            # Moderation roles
            'watchlistRoleID',
            # Miscellaneous roles
            'nitroRoleID', 'extrasRoleID', 'flexRoleID', 'verifiedRoleID', 'suspendedRoleID'
        ]
        
        channel_fields = [
            # Basic channels
            'moderation_logs', 'tickets_log_channel_id', 'transfer_log_channel_id',
            'update_logs_channel_id', 'BOT_LOGS_CHANNEL_ID', 'AutoMuteLogs',
            'GIVEAWAYS_CHANNEL_ID', 'tickets_category_id', 'verification_category_id',
            'MANAGEMENT_LOGS_ID', 'EXILE_LOGS_ID', 'BMT_LOGS_CHANNEL_ID',
            'EVENT_POSTS_CHANNEL_ID', 'TRYOUT_CATEGORY_ID', 'unfairMuteCategoryID',
            'MASS_CLOSURE_LOG_CHANNEL_ID', 'TICKET_CATEGORY_ID',
            # Verification channels
            'verification_logs_channel_id',
            # Moderation channels
            'moderationLogs',
            # Miscellaneous channels
            'colorsGuildID', 'shiftChannelID',
            # Event channels
            'SERVERSTARTUP_CHANNEL_ID', 'ACTIVITY_CHECK_CHANNEL_ID',
            # Log channels
            'joinLogs', 'leaveLogs', 'statsReport'
        ]
        
        for field in role_fields + channel_fields:
            coerce_int_field(merged_config, field)
        
        # Get roles and channels from Discord API
        roles = get_guild_roles(guild_id) or []
        channels = get_guild_channels(guild_id) or []
        bot_info = get_bot_info() or {'username': 'Royal Guard Bot', 'id': '1367420411922354196'}
        print("Rendering configure.html template")
        
        # Debug template variables
        print(f"Guild info: {guild_info}")
        print(f"Config keys: {list(config.keys()) if config else 'None'}")
        print(f"Roles count: {len(roles)}")
        print(f"Channels count: {len(channels)}")
        
        response = app.make_response(render_template('configure.html', 
                             guild=guild_info, 
                             config=merged_config,
                             roles=roles,
                             channels=channels,
                             user=session.get('user', {'username': 'User'}),
                             bot_info=bot_info))
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        print(f"CRITICAL ERROR in configure_guild: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Configuration Error</h1><p>Error: {str(e)}</p><a href='/dashboard'>Back to Dashboard</a>", 500

@app.route('/save_config/<guild_id>', methods=['POST'])
@login_required
def save_config(guild_id):
    user_guilds = get_user_guilds(session['access_token'])
    
    if not user_can_manage_guild(session['user']['id'], guild_id, user_guilds):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        config_data = request.json
        if not config_data:
            return jsonify({'success': False, 'message': 'No configuration data received'}), 400
            
        print(f"Saving config for guild {guild_id}: {len(config_data)} fields")
        config_data['guild_id'] = str(guild_id)  # Ensure string consistency
        config_data['updated_at'] = datetime.utcnow()
        config_data['updated_by'] = session['user']['id']
        
        # Update or insert config
        result = db.guild_configs.update_one(
            {'guild_id': str(guild_id)},  # Ensure string consistency
            {'$set': config_data},
            upsert=True
        )
        
        print(f"Database update result: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id}")
        
        return jsonify({'success': True, 'message': 'Configuration saved successfully'})
    except Exception as e:
        print(f"Error saving config: {e}")
        import traceback
        traceback.print_exc()
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

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'Royal Guard Bot Dashboard'}, 200

# Ultra-fast liveness route (plain text)
@app.route('/ping')
def ping():
    return "pong", 200, {"Content-Type": "text/plain; charset=utf-8"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)