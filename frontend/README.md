# MyFinGPT-POC-V2 Frontend

React + TypeScript frontend for MyFinGPT-POC-V2 application.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

The frontend runs on `http://localhost:3000` by default.

### Environment Variables

Create a `.env` file in the frontend directory (optional):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_API_KEY=key1
```

**Note**: If you don't create a `.env` file, it defaults to:
- API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000`
- API Key: `key1`

## Features

### Phase 7 Implementation

- ✅ React application structure (Vite + TypeScript)
- ✅ Chat interface (message display, input)
- ✅ Analysis panel (report display with markdown)
- ✅ WebSocket integration (real-time progress updates)
- ✅ API client (REST endpoints)
- ✅ Session management
- ✅ Basic UI components (Button, Input, Loading)

### Components

- **Chat Interface**: Message list, message bubbles, chat input
- **Analysis Panel**: Report display with markdown rendering, citations, errors
- **Layout**: Two-column layout (50/50 split)
- **State Management**: React Context API

## API Integration

The frontend connects to the backend API at `/api/agents/execute` for agent execution and `/ws/progress/{session_id}` for WebSocket progress updates.

### Authentication

The frontend uses API key authentication. Sessions are automatically created and stored in localStorage.

## Project Structure

```
src/
├── components/          # React components
│   ├── Chat/           # Chat interface components
│   ├── Analysis/      # Analysis panel components
│   ├── Layout/        # Layout components
│   └── ui/            # Basic UI components
├── context/           # React Context providers
├── services/          # API and WebSocket clients
├── types/             # TypeScript type definitions
├── config/           # Configuration
├── App.tsx           # Main app component
└── main.tsx          # Entry point
```

## Code Quality

```bash
# Lint
npm run lint

# Format
npm run format
```

## Notes

- WebSocket endpoint `/ws/progress/{session_id}` needs to be implemented in the backend (Phase 7 assumes it will be available)
- The frontend extracts stock symbols from user input using simple pattern matching
- Session persistence uses localStorage
- Markdown rendering uses `react-markdown`
