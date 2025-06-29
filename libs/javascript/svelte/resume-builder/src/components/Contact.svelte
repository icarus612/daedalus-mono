<script lang="ts">
  interface PersonalInfo {
    phone: string;
    email: string;
    location: string;
  }
  
  let { personalInfo }: { personalInfo: PersonalInfo } = $props();
  
  let formData = $state({
    name: '',
    email: '',
    message: ''
  });
  
  let isSubmitting = $state(false);
  let submitMessage = $state('');
  
  async function handleSubmit(e: Event) {
    e.preventDefault();
    isSubmitting = true;
    submitMessage = '';
    
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        submitMessage = 'Thank you for your message! I\'ll get back to you soon.';
        formData = { name: '', email: '', message: '' };
      } else {
        submitMessage = 'Something went wrong. Please try again.';
      }
    } catch (error) {
      submitMessage = 'Something went wrong. Please try again.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<section class="min-h-screen flex items-center justify-center py-20 bg-gray-900">
  <div class="container mx-auto px-4">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
      <div class="space-y-6">
        <h2 class="text-3xl font-bold text-white">CONTACT ME</h2>
        <div class="space-y-4">
          <div class="flex items-center gap-4">
            <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span class="text-lg">{personalInfo.phone}</span>
          </div>
          <div class="flex items-center gap-4">
            <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span class="text-lg">{personalInfo.email}</span>
          </div>
          <div class="flex items-center gap-4">
            <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="text-lg">{personalInfo.location}</span>
          </div>
        </div>
      </div>
      
      <div>
        <form class="space-y-6" onsubmit={handleSubmit}>
          <div class="form-control">
            <input 
              bind:value={formData.name}
              name="name" 
              type="text" 
              placeholder="Your Name" 
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
              required
              disabled={isSubmitting}
            />
          </div>
          <div class="form-control">
            <input 
              bind:value={formData.email}
              name="email" 
              type="email" 
              placeholder="Your Email" 
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
              required
              disabled={isSubmitting}
            />
          </div>
          <div class="form-control">
            <textarea 
              bind:value={formData.message}
              name="message" 
              rows="5" 
              placeholder="Your Message" 
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
              required
              disabled={isSubmitting}
            ></textarea>
          </div>
          <button 
            type="submit" 
            class="w-full py-3 bg-transparent border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-black transition-all duration-300"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Sending...' : 'SEND MESSAGE'}
          </button>
          {#if submitMessage}
            <div class="p-4 rounded-lg {submitMessage.includes('Thank you') ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}">
              <span>{submitMessage}</span>
            </div>
          {/if}
        </form>
      </div>
    </div>
  </div>
</section>