<script lang="ts">
  interface NavItem {
    href: string;
    label: string;
  }
  
  interface PersonalInfo {
    brandName: string;
  }
  
  let { 
    navItems = [], 
    personalInfo 
  }: { 
    navItems: NavItem[]; 
    personalInfo: PersonalInfo 
  } = $props();
  
  let isMenuOpen = $state(false);
  
  function toggleMenu() {
    isMenuOpen = !isMenuOpen;
  }
  
  function closeMenu() {
    isMenuOpen = false;
  }
</script>

<nav class="bg-black/90 backdrop-blur-sm shadow-lg fixed top-0 z-50 w-full px-4 py-4">
  <div class="flex items-center justify-between w-full max-w-7xl mx-auto">
    <div class="flex items-center">
      <a class="text-2xl font-bold text-primary" href="#home">{personalInfo.brandName}</a>
    </div>
    <div class="hidden lg:flex items-center space-x-8">
      {#each navItems as item}
        <a href={item.href} class="text-gray-300 hover:text-primary transition-colors duration-300">{item.label}</a>
      {/each}
    </div>
    <div class="lg:hidden">
      <button 
        class="text-white p-2"
        onclick={toggleMenu}
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </div>
  </div>
</nav>

{#if isMenuOpen}
  <div class="fixed inset-0 bg-black/50 z-40 lg:hidden" onclick={closeMenu}></div>
  <div class="fixed top-0 right-0 w-64 h-full bg-gray-900 z-50 lg:hidden transform transition-transform duration-300">
    <div class="p-6">
      <button onclick={closeMenu} class="absolute top-4 right-4 text-white">
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      <ul class="mt-8 space-y-4">
        {#each navItems as item}
          <li><a href={item.href} onclick={closeMenu} class="block text-gray-300 hover:text-primary transition-colors duration-300 text-lg">{item.label}</a></li>
        {/each}
      </ul>
    </div>
  </div>
{/if}