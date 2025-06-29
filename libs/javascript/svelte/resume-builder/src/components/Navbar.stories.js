import Navbar from './Navbar.svelte';

export default {
  title: 'Components/Navbar',
  component: Navbar,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    navItems: {
      control: 'object',
    },
    personalInfo: {
      control: 'object',
    },
  },
};

export const Default = {
  args: {
    personalInfo: {
      brandName: 'John Doe',
    },
    navItems: [
      { href: '#home', label: 'Home' },
      { href: '#about', label: 'About' },
      { href: '#services', label: 'Services' },
      { href: '#portfolio', label: 'Portfolio' },
      { href: '#contact', label: 'Contact' },
    ],
  },
};

export const MinimalNavigation = {
  args: {
    personalInfo: {
      brandName: 'Developer',
    },
    navItems: [
      { href: '#home', label: 'Home' },
      { href: '#work', label: 'Work' },
      { href: '#contact', label: 'Contact' },
    ],
  },
};