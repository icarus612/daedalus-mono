import Contact from './Contact.svelte';

export default {
  title: 'Components/Contact',
  component: Contact,
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
      phone: '+1 (555) 123-4567',
      email: 'john.doe@example.com',
      location: 'San Francisco, CA',
    },
  },
};

export const InternationalContact = {
  args: {
    personalInfo: {
      phone: '+44 20 1234 5678',
      email: 'jane.smith@example.co.uk',
      location: 'London, United Kingdom',
    },
  },
};

export const RemoteWorker = {
  args: {
    personalInfo: {
      phone: '+1 (555) 987-6543',
      email: 'alex.developer@remote.work',
      location: 'Remote / Worldwide',
    },
  },
};

export const MinimalContact = {
  args: {
    personalInfo: {
      phone: '555-0123',
      email: 'contact@dev.com',
      location: 'USA',
    },
  },
};