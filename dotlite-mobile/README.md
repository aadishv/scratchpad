# Dotlist Lite Mobile

A React Native mobile version of Dotlist Lite, providing the same elegant task management experience optimized for mobile devices.

## Features

- **Simple Task Management**: Create, edit, and organize tasks with red/yellow/green status indicators
- **Multiple Lists**: Organize tasks into different lists
- **Mobile-Optimized UI**: Native mobile interface with touch-friendly interactions
- **Real-time Sync**: Powered by Convex for real-time data synchronization
- **Cross-Platform**: Works on both iOS and Android

## Tech Stack

- **React Native**: Cross-platform mobile framework
- **Expo**: Development platform and tools
- **Convex**: Backend-as-a-Service for real-time data and authentication
- **TypeScript**: Type-safe development

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up Convex backend**:
   - Copy your Convex deployment URL to `.env` file
   - Or use the shared backend from the web version

3. **Start the development server**:
   ```bash
   npm start
   ```

4. **Run on device/simulator**:
   - Install Expo Go app on your phone
   - Scan the QR code from the terminal
   - Or run `npm run ios` / `npm run android` for simulators

## Project Structure

```
src/
├── components/
│   ├── auth/
│   │   └── AuthWrapper.tsx     # Authentication wrapper
│   └── multi-list/
│       ├── MultiListApp.tsx    # Main app component
│       ├── TopSection.tsx      # List header and navigation
│       └── BottomSection.tsx   # Task items and creation
├── App.tsx                     # Root app component
└── ...
```

## Key Differences from Web Version

- **Touch-First UI**: Optimized for touch interactions
- **Native Modals**: Using React Native modal components
- **Mobile Navigation**: Simplified navigation suitable for mobile
- **Touch Gestures**: Tap to change status, long press for actions
- **Mobile Typography**: Responsive text sizing for mobile screens

## Usage

1. **Authentication**: Tap "Get Started" to begin (anonymous authentication)
2. **Create Lists**: Use the menu button (⋮) to create or switch between lists
3. **Add Tasks**: Use the input field at the top to add new tasks
4. **Change Status**: Tap the colored circle to cycle through red → yellow → green
5. **Edit Tasks**: Tap on task text to edit
6. **Delete Tasks**: Tap the trash icon to delete

## Development

To contribute or modify:

1. Clone the repository
2. Follow setup instructions above
3. Make changes to components in `src/components/`
4. Test on both iOS and Android
5. Ensure backend compatibility with the web version

## Backend Compatibility

This mobile app shares the same Convex backend with the web version, ensuring:
- Data synchronization between web and mobile
- Consistent authentication
- Real-time updates across platforms