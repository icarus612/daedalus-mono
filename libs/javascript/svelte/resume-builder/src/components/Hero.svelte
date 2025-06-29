<script lang="ts">
  import { onMount } from 'svelte';
  
  interface PersonalInfo {
    name: string;
    rotatingTitles: string[];
    bio: string;
  }
  
  let { personalInfo }: { personalInfo: PersonalInfo } = $props();
  
  let rotatingText = $state(personalInfo.rotatingTitles[0]);
  let currentIndex = $state(0);
  
  onMount(() => {
    const interval = setInterval(() => {
      currentIndex = (currentIndex + 1) % personalInfo.rotatingTitles.length;
      rotatingText = personalInfo.rotatingTitles[currentIndex];
    }, 3000);
    
    return () => clearInterval(interval);
  });
</script>

<section class="hero min-h-screen flex items-center justify-center bg-cover bg-center bg-no-repeat relative" style="background-image: url('/images/home-bg.jpg')">
  <div class="absolute inset-0 bg-black/50"></div>
  <div class="container mx-auto px-4 relative z-10">
    <div class="text-center">
      <h1 class="inline-block text-4xl md:text-5xl font-bold mb-8 px-8 md:px-12 py-6 border-2 border-primary text-primary tracking-[6px] animate-fadeIn">
        {personalInfo.name}
      </h1>
      <h2 class="text-2xl md:text-3xl font-light mb-8 text-white transition-all duration-500">
        {rotatingText}
      </h2>
      <p class="text-lg md:text-xl max-w-3xl mx-auto text-gray-300">
        {personalInfo.bio}
      </p>
    </div>
  </div>
</section>

<style>
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fadeIn {
    animation: fadeIn 0.9s ease-out;
  }
  
  .hero {
    background-attachment: fixed;
  }
</style>