# OmniSearch Frontend

Next.js frontend for **OmniSearch: A Multimodal Retrieval and Ranking System for Cross-Modal E-Commerce Product Discovery**.

## Features

- 🔍 **Text Search** - Search products using natural language
- 🖼️ **Image Search** - Upload images to find similar products
- 🔀 **Multimodal Search** - Combine text and images for best results
- 📱 **Responsive Design** - Works on desktop and mobile
- 🌙 **Dark Mode** - Automatic dark/light theme support
- ⚡ **Real-time** - Live API status indicator

## Quick Start

### 1. Start the Backend API

First, make sure the OmniSearch API is running:

```bash
# From the root directory
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# API will be at http://localhost:8000
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx        # Main search page
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   ├── components/
│   │   ├── SearchBar.tsx   # Search input with filters
│   │   ├── ProductCard.tsx # Product display components
│   │   └── StatusBadge.tsx # API status indicator
│   └── lib/
│       └── api.ts          # API client functions
├── public/                  # Static assets
├── package.json
└── README.md
```

## API Integration

The frontend connects to these backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search/text` | POST | Text-based product search |
| `/search/image` | POST | Image-based product search |
| `/search/multimodal` | POST | Combined text + image search |
| `/search/health` | GET | API health check |

## Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Lint code
npm run lint
```

## Tech Stack

- **Next.js 15** - React framework
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling
- **Fetch API** - HTTP client

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in [Vercel](https://vercel.com)
3. Set environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

### Docker

```bash
# Build
docker build -t omnisearch-frontend .

# Run
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 omnisearch-frontend
```

## Screenshots

### Search Page
![Search Page](../docs/screenshots/search.png)

### Results Grid
![Results](../docs/screenshots/results.png)

---

Part of [OmniSearch](https://github.com/HustleDanie/OmniSearch-A-Multimodal-Retrieval-and-Ranking-System-for-Cross-Modal-E-Commerce-Product-Discovery)
