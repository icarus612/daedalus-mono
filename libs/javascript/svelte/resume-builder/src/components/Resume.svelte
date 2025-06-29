<script lang="ts">
  import { onMount } from 'svelte';
  import Hero from './Hero.svelte';
  import Services from './Services.svelte';
  import Skills from './Skills.svelte';
  import Portfolio from './Portfolio.svelte';
  import Contact from './Contact.svelte';

  interface Section {
    type: string;
    name: string;
    title: string;
  }

  interface ResumeData {
    sections: Section[];
    personalInfo: any;
    services: any[];
    skills: any[];
    projects: any[];
    navigation: any[];
  }

  let { resumeData }: { resumeData: ResumeData } = $props();
  
  function getSectionComponent(type: string) {
    switch (type) {
      case 'hero': return Hero;
      case 'services': return Services;
      case 'skills': return Skills;
      case 'portfolio': return Portfolio;
      case 'contact': return Contact;
      default: return null;
    }
  }
  
  function getSectionProps(type: string): any {
    switch (type) {
      case 'hero': 
        return { personalInfo: resumeData.personalInfo };
      case 'services': 
        return { services: resumeData.services };
      case 'skills': 
        return { skillGroups: resumeData.skills };
      case 'portfolio': 
        return { projects: resumeData.projects };
      case 'contact': 
        return { personalInfo: resumeData.personalInfo };
      default: 
        return {};
    }
  }
</script>

{#each resumeData.sections as section}
  <div id={section.name}>
    {#if getSectionComponent(section.type)}
      <svelte:component this={getSectionComponent(section.type)} {...getSectionProps(section.type)} />
    {/if}
  </div>
{/each}

