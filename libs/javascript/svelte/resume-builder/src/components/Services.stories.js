import Services from './Services.svelte';

export default {
  title: 'Components/Services',
  component: Services,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    services: {
      control: 'object',
    },
  },
};

export const Default = {
  args: {
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
  },
};

export const SingleService = {
  args: {
    services: [
      {
        icon: 'laptop',
        title: 'Full Stack Development',
        description: 'End-to-end development of web applications from frontend to backend, including database design and deployment.',
      },
    ],
  },
};

export const ExtensiveServices = {
  args: {
    services: [
      {
        icon: 'laptop',
        title: 'Frontend Development',
        description: 'Building interactive user interfaces with React, Vue, Svelte, and other modern frameworks.',
      },
      {
        icon: 'link',
        title: 'Backend Development',
        description: 'Developing robust server-side applications with Node.js, Python, and database integration.',
      },
      {
        icon: 'default',
        title: 'Mobile Development',
        description: 'Creating cross-platform mobile applications using React Native and Flutter.',
      },
      {
        icon: 'laptop',
        title: 'DevOps & Deployment',
        description: 'Setting up CI/CD pipelines, containerization with Docker, and cloud infrastructure management.',
      },
      {
        icon: 'link',
        title: 'UI/UX Design',
        description: 'Designing user-centered interfaces with a focus on usability and aesthetic appeal.',
      },
      {
        icon: 'default',
        title: 'Technical Consulting',
        description: 'Providing technical guidance and architecture recommendations for complex projects.',
      },
    ],
  },
};