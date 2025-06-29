import Portfolio from './Portfolio.svelte';

export default {
  title: 'Components/Portfolio',
  component: Portfolio,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    projects: {
      control: 'object',
    },
  },
};

export const Default = {
  args: {
    projects: [
      {
        title: 'E-Commerce Platform',
        subtitle: 'Full Stack Application',
        techStack: 'React, Node.js, MongoDB',
        image: 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=500&h=500&fit=crop',
        link: 'https://example.com/ecommerce',
        description: 'A comprehensive e-commerce solution with payment integration and inventory management.',
      },
      {
        title: 'Task Management App',
        subtitle: 'Productivity Tool',
        techStack: 'Svelte, Firebase, Tailwind CSS',
        image: 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=500&h=500&fit=crop',
        link: 'https://example.com/taskmanager',
        description: 'A modern task management application with real-time collaboration features.',
      },
      {
        title: 'Weather Dashboard',
        subtitle: 'Data Visualization',
        techStack: 'Vue.js, D3.js, OpenWeather API',
        image: 'https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=500&h=500&fit=crop',
        link: 'https://example.com/weather',
        description: 'Interactive weather dashboard with charts and forecasting capabilities.',
      },
    ],
  },
};

export const SingleProject = {
  args: {
    projects: [
      {
        title: 'Portfolio Website',
        subtitle: 'Personal Branding',
        techStack: 'Svelte, TailwindCSS, Vercel',
        image: 'https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=500&h=500&fit=crop',
        link: 'https://example.com/portfolio',
        description: 'A clean and responsive portfolio website showcasing development skills.',
      },
    ],
  },
};

export const ExtensivePortfolio = {
  args: {
    projects: [
      {
        title: 'Social Media Dashboard',
        subtitle: 'Analytics Platform',
        techStack: 'React, TypeScript, GraphQL',
        image: 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=500&h=500&fit=crop',
        link: 'https://example.com/social-dashboard',
        description: 'Comprehensive social media analytics and management platform.',
      },
      {
        title: 'Learning Management System',
        subtitle: 'Educational Platform',
        techStack: 'Next.js, PostgreSQL, Stripe',
        image: 'https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=500&h=500&fit=crop',
        link: 'https://example.com/lms',
        description: 'Online learning platform with course management and payment processing.',
      },
      {
        title: 'Restaurant Booking App',
        subtitle: 'Mobile Application',
        techStack: 'React Native, Firebase, Maps API',
        image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&h=500&fit=crop',
        link: 'https://example.com/restaurant-app',
        description: 'Mobile app for restaurant reservations with location-based search.',
      },
      {
        title: 'Cryptocurrency Tracker',
        subtitle: 'Financial Dashboard',
        techStack: 'Vue.js, Chart.js, CoinGecko API',
        image: 'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=500&h=500&fit=crop',
        link: 'https://example.com/crypto-tracker',
        description: 'Real-time cryptocurrency price tracking with portfolio management.',
      },
      {
        title: 'Fitness Tracking App',
        subtitle: 'Health & Wellness',
        techStack: 'Flutter, Dart, HealthKit API',
        image: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
        link: 'https://example.com/fitness-app',
        description: 'Comprehensive fitness tracking with workout plans and progress analytics.',
      },
      {
        title: 'Music Streaming Platform',
        subtitle: 'Entertainment App',
        techStack: 'Angular, Node.js, AWS S3',
        image: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=500&h=500&fit=crop',
        link: 'https://example.com/music-platform',
        description: 'Music streaming service with playlist management and social features.',
      },
    ],
  },
};