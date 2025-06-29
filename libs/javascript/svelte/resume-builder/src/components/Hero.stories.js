import Hero from './Hero.svelte';

export default {
  title: 'Components/Hero',
  component: Hero,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    personalInfo: {
      control: 'object',
    },
  },
};

export const Default = {
  args: {
    personalInfo: {
      name: 'John Doe',
      rotatingTitles: ['Full Stack Developer', 'UI/UX Designer', 'Software Engineer'],
      bio: 'Passionate developer with 5+ years of experience creating amazing web applications and user experiences.',
    },
  },
};

export const WithLongBio = {
  args: {
    personalInfo: {
      name: 'Jane Smith',
      rotatingTitles: ['Senior Developer', 'Tech Lead', 'Architect'],
      bio: 'Experienced software engineer with a strong background in full-stack development, system architecture, and team leadership. Specializing in modern web technologies and scalable solutions.',
    },
  },
};