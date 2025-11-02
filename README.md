# Markdown Editor

A beautiful Markdown editor built with React, Lexical, and Vite, featuring Discord-style syntax highlighting.

## Features

- **Bold** text using `**text**` or `__text__`
- *Italic* text using `*text*` or `_text_`
- ~~Strikethrough~~ text using `~~text~~`
- Headings (H1-H6) using `#` through `######`
- Unordered lists using `-` or `*`
- Ordered lists using `1.`, `2.`, etc.
- Discord-style syntax highlighting where special markdown characters are grayed out (50% opacity)

## Screenshots

### Editor in Action
![Markdown Editor](https://github.com/user-attachments/assets/11e92117-7601-4208-a758-a77ba4d0f2ab)

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

### Development

Run the development server:

```bash
npm run dev
```

The editor will be available at `http://localhost:5173/`

### Build

Build for production:

```bash
npm run build
```

### Preview

Preview the production build:

```bash
npm run preview
```

## Technology Stack

- **React 19** - UI library
- **Lexical** - Extensible text editor framework by Meta
- **Vite** - Fast build tool and development server
- **TypeScript** - Type safety

## Implementation Details

The editor uses a custom `MarkdownTextNode` that extends Lexical's `TextNode` to parse markdown syntax in real-time and apply Discord-style formatting. Special syntax characters are wrapped in spans with reduced opacity to create the signature grayed-out effect.

## License

ISC
