import Skills from './Skills.svelte';

export default {
  title: 'Components/Skills',
  component: Skills,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    skillGroups: {
      control: 'object',
    },
  },
};

export const Default = {
  args: {
    skillGroups: [
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
  },
};

export const SingleSkillGroup = {
  args: {
    skillGroups: [
      {
        title: 'Programming Languages',
        skills: [
          { name: 'TypeScript', percentage: 95 },
          { name: 'JavaScript', percentage: 90 },
          { name: 'Python', percentage: 80 },
          { name: 'Java', percentage: 70 },
          { name: 'Go', percentage: 60 },
        ],
      },
    ],
  },
};