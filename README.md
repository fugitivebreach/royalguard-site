# Royal Guard Bot Dashboard

A modern web dashboard for managing your Royal Guard Discord bot configuration with a beautiful gold-to-red gradient theme.

## Features

- **Discord OAuth Integration** - Secure login with Discord
- **Server Management** - Configure bot settings for servers you own or administrate
- **MongoDB Integration** - All configurations stored in MongoDB
- **Role & Channel Selection** - Easy dropdowns for Discord roles and channels
- **Custom Configuration** - Manage blacklisted groups, whitelisted groups, API tokens, and more
- **Responsive Design** - Works perfectly on desktop and mobile
- **Real-time Updates** - Instant configuration saving and loading

## Setup Instructions

### 1. Discord Application Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or use your existing bot application
3. Go to OAuth2 → General and add your redirect URI:
   - For local development: `http://localhost:5000/callback`
   - For Railway: `https://your-app-name.railway.app/callback`
4. Note down your Client ID and Client Secret
5. Go to Bot section and copy your Bot Token

### 2. Environment Configuration

1. Copy `.env.example` to `.env`
2. Fill in your Discord credentials:
   ```
   DISCORD_CLIENT_ID=your_client_id
   DISCORD_CLIENT_SECRET=your_client_secret
   DISCORD_BOT_TOKEN=your_bot_token
   REDIRECT_URI=https://your-app-name.railway.app/callback
   ```

### 3. Railway Deployment

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize project: `railway init`
4. Deploy: `railway up`
5. Set environment variables in Railway dashboard
6. Your app will be available at: `https://your-app-name.railway.app`

### 4. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run the application
python app.py
```

## Configuration Options

The dashboard allows you to configure:

### Role Settings
- Support Role
- Moderator Role  
- Administrator Role
- Suspended Role
- Verified Role
- Nitro Role

### Channel Settings
- Moderation Logs
- Tickets Log Channel
- Tickets Category
- Update Logs Channel

### API Tokens
- RoWifi API Token
- Trello API Key
- Trello API Token

### Custom Lists
- Blacklisted Groups
- Whitelisted Groups
- Blacklisted Names
- Groups to Check
- Color Roles
- Timezone Roles

## Database Schema

Configurations are stored in MongoDB with the following structure:

```json
{
  "guild_id": "1371945471207018497",
  "support_role_id": 1408978779723796480,
  "moderator_role_id": 1408978777530175649,
  "blacklisted_groups": [2621202, 4972535],
  "whitelisted_groups": [15356653],
  "updated_at": "2024-01-01T00:00:00Z",
  "updated_by": "user_id"
}
```

## Security Features

- **Owner Protection** - Bot owners (defined in code) have access to all servers
- **Permission Checking** - Users must be server owner or have administrator permissions
- **Secure Sessions** - Flask sessions with secure secret keys
- **Input Validation** - All inputs are validated before saving

## Styling

The dashboard features a modern design with:
- Gold to red gradient theme
- Glassmorphism effects
- Smooth animations and transitions
- Responsive mobile design
- Dark theme optimized for Discord users

## Support

For support or questions, contact the bot owners as defined in `configuration/config.py`.
