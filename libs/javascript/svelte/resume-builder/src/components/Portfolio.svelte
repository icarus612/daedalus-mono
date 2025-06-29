<script lang="ts">
  interface Project {
    title: string;
    subtitle: string;
    techStack: string;
    image: string;
    link: string;
    description?: string;
  }

  let { projects = [] }: { projects: Project[] } = $props();
</script>

<section class="min-h-screen flex items-center justify-center py-20 bg-black">
  <div class="container mx-auto px-4">
    <h2 class="text-4xl md:text-5xl font-bold text-center mb-16">PROJECTS</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {#each projects as project}
        <a href={project.link} target="_blank" rel="noopener noreferrer" class="group">
          <div class="bg-gray-900 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden rounded-lg">
            <figure class="relative aspect-square overflow-hidden">
              <img 
                src={project.image} 
                alt={project.title}
                class="object-cover w-full h-full group-hover:scale-110 transition-transform duration-300"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-6">
                <div class="text-white">
                  <h4 class="text-xl font-bold mb-2">{project.subtitle}</h4>
                  <p class="text-sm">{project.techStack}</p>
                </div>
              </div>
            </figure>
            <div class="p-4">
              <h3 class="text-lg font-semibold text-white">{project.title}</h3>
            </div>
          </div>
        </a>
      {/each}
    </div>
  </div>
</section>