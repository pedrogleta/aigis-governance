# Aigis Governance Frontend

A modern React + Vite interface for the AI Agent system that allows users to chat with AI agents for data analysis and visualization.

## Features

- 🎨 **Dark & Green Theme** - Modern, professional interface with excellent contrast
- 💬 **Real-time Chat** - Interactive chat interface with the AI agents
- 📊 **Data Visualization** - Support for displaying generated plots and charts
- 💻 **Code Display** - Syntax-highlighted code blocks for analysis scripts
- 🔄 **Session Management** - Persistent chat sessions across page reloads
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

- **React 19** - Latest React with modern hooks and patterns
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful, customizable icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Configuration

The frontend is configured to connect to the backend at `http://localhost:8000` by default. You can modify this in `src/services/api.ts`.

## API Integration

The frontend expects the following API endpoints from your backend:

- `POST /api/chat` - Send chat messages and receive responses
- `GET /health` - Health check endpoint

## Project Structure

```
src/
├── components/          # React components
├── services/           # API and external services
├── lib/               # Utility functions
├── App.tsx            # Main application component
├── main.tsx           # Application entry point
└── index.css          # Global styles and Tailwind imports
```

## Customization

### Theme Colors

The dark and green theme can be customized in `tailwind.config.js`:

```javascript
colors: {
  primary: {
    // Green color palette
    500: '#22c55e', // Main green
    // ... other shades
  },
  dark: {
    // Dark color palette
    950: '#020617', // Background
    // ... other shades
  }
}
```

### Styling

Custom CSS classes are defined in `src/index.css` using Tailwind's `@layer` directive.

## Development

### Code Style

- Use TypeScript for all new code
- Follow React best practices and hooks patterns
- Use Tailwind CSS classes for styling
- Keep components small and focused

### Adding New Features

1. Create new components in `src/components/`
2. Add new API methods in `src/services/api.ts`
3. Update types and interfaces as needed
4. Test thoroughly before committing

## Troubleshooting

### Common Issues

1. **Tailwind CSS not working**: Make sure `tailwind.config.js` and `postcss.config.js` are properly configured
2. **API connection errors**: Check that your backend is running and accessible
3. **Build errors**: Ensure all dependencies are installed with `npm install`

### Getting Help

- Check the console for error messages
- Verify your backend is running and accessible
- Ensure all environment variables are set correctly

## License

This project is part of Aigis Governance and follows the same licensing terms.
