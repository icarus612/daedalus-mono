import Resume from './Resume.svelte';

export default {
  title: 'Components/Resume',
  component: Resume,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    resumeData: {
      control: 'object',
    },
  },
};

export const Default = {
  args: {
    resumeData: {
      sections: [
        { type: 'hero', name: 'home', title: 'Home' },
        { type: 'services', name: 'services', title: 'Services' },
        { type: 'skills', name: 'skills', title: 'Skills' },
        { type: 'portfolio', name: 'portfolio', title: 'Portfolio' },
        { type: 'contact', name: 'contact', title: 'Contact' },
      ],
      personalInfo: {
        name: 'John Doe',
        rotatingTitles: ['Full Stack Developer', 'UI/UX Designer', 'Software Engineer'],
        bio: 'Passionate developer with 5+ years of experience creating amazing web applications and user experiences.',
        phone: '+1 (555) 123-4567',
        email: 'john.doe@example.com',
        location: 'San Francisco, CA',
      },
      services: [
        {
          icon: 'laptop',
          title: 'Web Development',
          description: 'Creating responsive and modern web applications using the latest technologies and best practices.',
        },
        {
          icon: 'link',
          title: 'API Integration',
          description: 'Building and integrating RESTful APIs and third-party services for seamless data flow.',
        },
        {
          icon: 'default',
          title: 'Performance Optimization',
          description: 'Optimizing web applications for speed, performance, and better user experience.',
        },
      ],
      skills: [
        {
          title: 'Frontend Development',
          skills: [
            { name: 'JavaScript', percentage: 90 },
            { name: 'React', percentage: 85 },
            { name: 'Svelte', percentage: 80 },
            { name: 'CSS/SCSS', percentage: 85 },
          ],
        },
        {
          title: 'Backend Development',
          skills: [
            { name: 'Node.js', percentage: 80 },
            { name: 'Python', percentage: 75 },
            { name: 'PostgreSQL', percentage: 70 },
            { name: 'MongoDB', percentage: 65 },
          ],
        },
      ],
      projects: [
        {
          title: 'E-Commerce Platform',
          subtitle: 'Full Stack Application',
          techStack: 'React, Node.js, MongoDB',
          image: 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=500&h=500&fit=crop',
          link: 'https://example.com/ecommerce',
        },
        {
          title: 'Task Management App',
          subtitle: 'Productivity Tool',
          techStack: 'Svelte, Firebase, Tailwind CSS',
          image: 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=500&h=500&fit=crop',
          link: 'https://example.com/taskmanager',
        },
      ],
      navigation: [
        { href: '#home', label: 'Home' },
        { href: '#services', label: 'Services' },
        { href: '#skills', label: 'Skills' },
        { href: '#portfolio', label: 'Portfolio' },
        { href: '#contact', label: 'Contact' },
      ],
    },
  },
};

export const MinimalResume = {
  args: {
    resumeData: {
      sections: [
        { type: 'hero', name: 'home', title: 'Home' },
        { type: 'contact', name: 'contact', title: 'Contact' },
      ],
      personalInfo: {
        name: 'Jane Smith',
        rotatingTitles: ['Developer'],
        bio: 'Software developer specializing in web technologies.',
        phone: '+1 (555) 987-6543',
        email: 'jane.smith@example.com',
        location: 'New York, NY',
      },
      services: [],
      skills: [],
      projects: [],
      navigation: [
        { href: '#home', label: 'Home' },
        { href: '#contact', label: 'Contact' },
      ],
    },
  },
};

export const FullResume = {
  args: {
    resumeData: {
      sections: [
        { type: 'hero', name: 'home', title: 'Home' },
        { type: 'services', name: 'services', title: 'Services' },
        { type: 'skills', name: 'skills', title: 'Skills' },
        { type: 'portfolio', name: 'portfolio', title: 'Portfolio' },
        { type: 'contact', name: 'contact', title: 'Contact' },
      ],
      personalInfo: {
        name: 'Alex Johnson',
        rotatingTitles: ['Senior Full Stack Developer', 'Tech Lead', 'Software Architect', 'Open Source Contributor'],
        bio: 'Experienced software engineer with 8+ years in full-stack development, leading teams and architecting scalable solutions. Passionate about clean code, performance optimization, and mentoring junior developers.',
        phone: '+1 (555) 246-8135',
        email: 'alex.johnson@techexpert.dev',
        location: 'Seattle, WA',
      },
      services: [
        {
          icon: 'laptop',
          title: 'Full Stack Development',
          description: 'End-to-end development of scalable web applications using modern frameworks and best practices.',
        },
        {
          icon: 'link',
          title: 'System Architecture',
          description: 'Designing and implementing robust, scalable system architectures for enterprise applications.',
        },
        {
          icon: 'default',
          title: 'Team Leadership',
          description: 'Leading development teams, mentoring junior developers, and establishing engineering best practices.',
        },
        {
          icon: 'laptop',
          title: 'DevOps & Cloud',
          description: 'Setting up CI/CD pipelines, containerization, and managing cloud infrastructure on AWS/GCP.',
        },
        {
          icon: 'link',
          title: 'Performance Optimization',
          description: 'Analyzing and optimizing application performance, reducing load times and improving user experience.',
        },
        {
          icon: 'default',
          title: 'Technical Consulting',
          description: 'Providing technical guidance and strategic recommendations for complex software projects.',
        },
      ],
      skills: [
        {
          title: 'Frontend Technologies',
          skills: [
            { name: 'React', percentage: 95 },
            { name: 'TypeScript', percentage: 90 },
            { name: 'Svelte', percentage: 85 },
            { name: 'Vue.js', percentage: 80 },
            { name: 'Next.js', percentage: 88 },
          ],
        },
        {
          title: 'Backend Technologies',
          skills: [
            { name: 'Node.js', percentage: 92 },
            { name: 'Python', percentage: 85 },
            { name: 'Go', percentage: 75 },
            { name: 'PostgreSQL', percentage: 88 },
            { name: 'MongoDB', percentage: 80 },
          ],
        },
        {
          title: 'DevOps & Tools',
          skills: [
            { name: 'Docker', percentage: 85 },
            { name: 'Kubernetes', percentage: 78 },
            { name: 'AWS', percentage: 82 },
            { name: 'CI/CD', percentage: 90 },
            { name: 'Terraform', percentage: 70 },
          ],
        },
      ],
      projects: [
        {
          title: 'Enterprise CRM System',
          subtitle: 'Large Scale Application',
          techStack: 'React, Node.js, PostgreSQL, AWS',
          image: 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=500&h=500&fit=crop',
          link: 'https://example.com/crm-system',
        },
        {
          title: 'Microservices Architecture',
          subtitle: 'Backend Infrastructure',
          techStack: 'Go, Docker, Kubernetes, gRPC',
          image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=500&h=500&fit=crop',
          link: 'https://example.com/microservices',
        },
        {
          title: 'Real-time Analytics Dashboard',
          subtitle: 'Data Visualization',
          techStack: 'Svelte, D3.js, WebSockets, InfluxDB',
          image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500&h=500&fit=crop',
          link: 'https://example.com/analytics-dashboard',
        },
        {
          title: 'Mobile Banking App',
          subtitle: 'Fintech Application',
          techStack: 'React Native, Node.js, MongoDB, Stripe',
          image: 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=500&h=500&fit=crop',
          link: 'https://example.com/banking-app',
        },
        {
          title: 'AI-Powered Chatbot',
          subtitle: 'Machine Learning Integration',
          techStack: 'Python, TensorFlow, FastAPI, React',
          image: 'https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=500&h=500&fit=crop',
          link: 'https://example.com/ai-chatbot',
        },
        {
          title: 'E-learning Platform',
          subtitle: 'Educational Technology',
          techStack: 'Next.js, Prisma, PostgreSQL, Stripe',
          image: 'https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=500&h=500&fit=crop',
          link: 'https://example.com/elearning-platform',
        },
      ],
      navigation: [
        { href: '#home', label: 'Home' },
        { href: '#services', label: 'Services' },
        { href: '#skills', label: 'Skills' },
        { href: '#portfolio', label: 'Portfolio' },
        { href: '#contact', label: 'Contact' },
      ],
    },
  },
};