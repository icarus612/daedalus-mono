<script lang="ts">
  interface Skill {
    name: string;
    percentage: number;
  }
  
  interface SkillGroup {
    title: string;
    skills: Skill[];
  }
  
  let { skillGroups = [] }: { skillGroups: SkillGroup[] } = $props();
</script>

<section class="min-h-screen flex items-center justify-center py-20 bg-gray-900">
  <div class="container mx-auto px-4">
    <h2 class="text-4xl md:text-5xl font-bold text-center mb-16">SKILLS</h2>
    
    <div class="space-y-16">
      {#each skillGroups as skillGroup}
        <div>
          <h4 class="text-2xl font-semibold mb-8 text-primary">{skillGroup.title}</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {#each skillGroup.skills as skill}
              <div>
                <div class="flex justify-between mb-2">
                  <span class="text-gray-300">{skill.name}</span>
                  <span class="text-sm text-gray-500">{skill.percentage}%</span>
                </div>
                <div class="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                  <div class="bg-primary h-full transition-all duration-500" style="width: {skill.percentage}%"></div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>