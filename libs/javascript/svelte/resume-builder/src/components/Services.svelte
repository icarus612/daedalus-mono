<script lang="ts">
  interface Service {
    icon: string;
    title: string;
    description: string;
  }
  
  let { services = [] }: { services: Service[] } = $props();
</script>

<section class="min-h-screen flex items-center justify-center py-20 bg-black">
  <div class="container mx-auto px-4">
    <h2 class="text-4xl md:text-5xl font-bold text-center mb-16">WHAT I DO</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      {#each services as service}
        <div class="p-6 transition-all duration-300 hover:transform hover:scale-105">
          <div>
            <div class="flex items-start gap-4">
              <div class="text-primary text-3xl">
                {#if service.icon === 'link'}
                  <svg class="w-10 h-10" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd" />
                  </svg>
                {:else if service.icon === 'laptop'}
                  <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                {:else}
                  <svg class="w-10 h-10" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                  </svg>
                {/if}
              </div>
              <div class="flex-1">
                <h3 class="text-xl mb-3 text-white">{service.title}</h3>
                <p class="text-gray-400">{service.description}</p>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>