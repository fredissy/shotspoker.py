# Shots Poker - Architecture Documentation

## Overview

Shots Poker is a real-time planning poker application designed for agile development teams. It provides synchronized voting sessions with persistent history, real-time collaboration, and flexible deployment options.

## Tech Stack

### Backend
- **Python 3** with **Flask 3.1.3** as the web framework
- **Flask-SocketIO 5.6.1** for real-time WebSocket communication
- **SQLAlchemy 2.0.48** ORM with PostgreSQL or SQLite support
- **Redis 7.3.0** for distributed state storage (optional, falls back to in-memory)
- **Gevent 25.9** for async/concurrent operations
- **Gunicorn 25.1.0** for production serving
- **Alembic** for database migrations

### Frontend
- **HTML5** with **Jinja2** templating engine
- **Bootstrap 5.3.8** for responsive UI components
- **Chart.js** for vote distribution visualization
- **Socket.IO Client v4.8.3** for real-time updates
- **Vanilla JavaScript** for client-side logic

## Application Architecture

### High-Level Flow
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Browser       │◄──►│  Flask App   │◄──►│  Database   │
│  (Socket.IO)    │    │ (SocketIO)   │    │ (SQLAlchemy)│
└─────────────────┘    └──────────────┘    └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    Redis     │
                       │ (Room State) │
                       └──────────────┘
```

### Core Components

#### 1. Entry Point (`app.py`)
- Patches gevent monkey for async compatibility
- Initializes and runs the SocketIO server

#### 2. Application Factory (`src/__init__.py`)
- Creates Flask app instance
- Configures database connections (PostgreSQL/SQLite)
- Sets up Redis for state storage (with in-memory fallback)
- Initializes SocketIO with gevent async mode
- Registers route blueprints

#### 3. Data Models (`src/model.py`)
**Persistent Storage (Database):**
- `TicketSession`: Records of completed voting rounds
  - `id`, `room_id`, `ticket_key`, `timestamp`, `is_public`, `final_average`
- `Vote`: Individual votes within sessions
  - `id`, `user_name`, `value`, `session_id` (FK to TicketSession)

#### 4. State Management (`src/state.py`)
**Ephemeral State (Redis/Memory):**
```json
{
  "created_at": "timestamp",
  "last_updated": "timestamp", 
  "active": boolean,
  "ticket_key": "PROJ-123",
  "ticket_url": "https://jira.com/browse/PROJ-123",
  "is_public": boolean,
  "votes": {"user_name": {"value": "5"}, ...},
  "revealed": boolean,
  "admin_sid": "socket_id",
  "participants": {
    "socket_id": {
      "name": "Alice", 
      "avatar": "👾", 
      "role": "voter"
    }
  },
  "queue": ["PROJ-124", "PROJ-125"],
  "timer_end": null_or_timestamp,
  "deck_config": ["0", "1", "2", "3", "5", "8", "13", "21", "∞", "?", "☕"]
}
```

#### 5. Storage Abstraction (`src/store.py`)
- Provides atomic operations with locking
- Abstracts Redis vs in-memory storage
- Implements `change_room()` context manager for safe state updates
- Auto-cleanup with TTL (7 days) to prevent memory leaks

## Route Organization

### HTTP Routes (`src/routes/main.py`)
- `GET /` → Login page
- `POST /login` → Session creation, room joining/creation
- `GET /room/<room_id>` → Voting interface
- `POST /logout` → Session cleanup
- `GET /history` → Vote history API

### SocketIO Event Handlers
- **`src/routes/rooms.py`**: Connection management, participant tracking
- **`src/routes/votes.py`**: Vote casting, revealing, reactions
- **`src/routes/queue.py`**: Ticket queue management
- **`src/routes/timer.py`**: Session timer control
- **`src/routes/roles.py`**: Voter/Observer role switching
- **`src/routes/admin.py`**: Admin panel with monitoring

## Key Features Implementation

### 1. Room Management
- **Room IDs**: Generated from word combinations (`res/names.txt`)
- **Session Auth**: Flask sessions with cookies (`room_id`, `user_name`, `user_role`)
- **Auto-join**: SocketIO validates session and joins room namespace

### 2. Voting Mechanism
```
Start Vote → Cast Votes (Hidden) → Reveal → Statistics → Save to DB
     ↓           ↓                    ↓          ↓           ↓
  Set active   Store in       Set revealed=true  Calculate  TicketSession
   ticket      room state                       consensus   + Vote records
```

### 3. Real-time Synchronization
- **State Updates**: Every action broadcasts `state_update` to room participants
- **WebSocket Events**: All interactions via SocketIO (no polling)
- **Atomic Updates**: `change_room()` ensures consistency across concurrent operations

### 4. User Management
- **Roles**: `voter` (can estimate) vs `observer` (read-only)
- **Avatars**: Deterministically assigned based on username hash (29 emoji options)
- **Online Status**: Tracked via SocketIO connection state

## Frontend Architecture

### Templates (`templates/`)
- `login.html.j2`: Authentication and room creation/joining
- `vote.html.j2`: Main voting interface with dynamic components
- `admin.html.j2`: Room monitoring and history search
- `partials/`: Reusable template components

### JavaScript Modules (`static/js/`)
- `main.js`: SocketIO connection and event handling
- `vote.js`: Voting actions and admin controls
- `vote-ui.js`: UI updates, participant display, chart rendering
- `vote-queue.js`: Queue management interface
- `login.js`: Authentication flow
- `theme.js`: Dark/light mode persistence

## Data Flow Patterns

### 1. Session Lifecycle
```
Login → Create/Join Room → Connect WebSocket → Sync State → Vote → Persist → History
```

### 2. Real-time Updates
```
User Action → SocketIO Event → State Mutation → Broadcast → UI Update (All Clients)
```

### 3. Vote Flow
```
Admin: start_vote → Users: cast_vote → State: collect votes → Admin: reveal_vote → 
State: calculate stats → DB: save session → Broadcast: final results
```

## Database Schema

### Tables
1. **`ticket_sessions`**
   - Primary storage for completed voting rounds
   - Links to associated votes via foreign key relationship

2. **`votes`** 
   - Individual vote records per user per session
   - Supports both numeric and symbolic values ("∞", "?", "☕")

### Migrations (`migrations/`)
- Alembic-managed schema evolution
- Current migrations: initial creation, username length increase

## Configuration & Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/db  # Optional: defaults to SQLite
REDIS_URL=redis://host:port/db                   # Optional: defaults to in-memory  
SECRET_KEY=your-secret-key                       # Required: Flask session signing
ADMIN_USERNAME=admin                             # Optional: admin panel access
ADMIN_PASSWORD=password                          # Optional: admin panel access
```

### Deployment Options

#### Single Server (Development)
- **State**: In-memory storage
- **Database**: SQLite (`shotspoker.db`)
- **Scaling**: Single process only

#### Production (Recommended)
- **State**: Redis with persistence
- **Database**: PostgreSQL with connection pooling
- **Web Server**: Gunicorn with multiple workers
- **Load Balancer**: Nginx (if multiple app servers)

#### Docker Deployment
```dockerfile
# Uses included Dockerfile + entrypoint.sh for containerization
# Supports all deployment modes via environment variables
```

## File Structure Overview

```
├── app.py                 # Entry point
├── wsgi.py               # WSGI server interface  
├── src/                  # Core application
│   ├── __init__.py       # App factory
│   ├── model.py          # SQLAlchemy models
│   ├── state.py          # State management
│   ├── store.py          # Storage abstraction
│   ├── utils.py          # Utilities
│   └── routes/           # Route handlers
├── templates/            # Jinja2 templates
├── static/               # CSS, JS, images
├── migrations/           # Database migrations
├── res/                  # Resources (word lists)
├── requirements.txt      # Python dependencies
└── Dockerfile           # Container definition
```

## Security Considerations

1. **Session Management**: Flask sessions with server-side validation
2. **Admin Panel**: HTTP Basic Auth protection  
3. **Input Validation**: Ticket key format validation, username length limits
4. **Rate Limiting**: Natural rate limiting via SocketIO connection limits
5. **State Isolation**: Room-based state separation prevents cross-contamination

## Performance Characteristics

- **Concurrency**: Gevent-based async handling
- **State Storage**: Atomic operations with distributed locking
- **Memory Management**: Automatic cleanup with TTL expiration
- **Real-time Latency**: Sub-100ms for typical voting interactions
- **Scalability**: Horizontal scaling via Redis + multiple app servers

## Extension Points

1. **Custom Decks**: Extend deck configurations in voting logic
2. **Integrations**: Jira API integration for ticket details
3. **Authentication**: Plugin architecture for enterprise SSO
4. **Notifications**: Email/Slack notifications for session completion
5. **Analytics**: Extended metrics and reporting capabilities
6. **Feature Announcements**: Update `features.json` to announce new features to users

## Recent Feature Additions

### Feature Notification System
- **Version Tracking**: Uses build timestamps from `app.py` modification time
- **Feature Definitions**: Managed via `features.json` configuration file
- **User Tracking**: Client-side localStorage to remember last seen version
- **API Endpoints**: 
  - `/api/version` - Current version info with optional new features since timestamp
  - `/api/features` - All available features grouped by version
- **UI Integration**: Bootstrap modal displays feature announcements after login
- **Template**: `templates/partials/features.html.j2` contains modal and JavaScript logic

**Configuration Structure** (`features.json`):
```json
{
  "1743436800": {
    "version_name": "April 2026 Update",
    "features": [
      {
        "title": "Feature Name",
        "description": "Description of the new feature",
        "icon": "🔔" 
      }
    ]
  }
}
```

---

This architecture supports the core planning poker workflow while maintaining flexibility for future enhancements and deployment scenarios.