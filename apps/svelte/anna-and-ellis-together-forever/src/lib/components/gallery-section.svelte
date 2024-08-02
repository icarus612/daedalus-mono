<script>
	import { ImageModal } from '$components';
	import Image from './image.svelte';

	export let images = [];
	let currentImage = false;
	
</script>

<div>
	{#if currentImage}
		<ImageModal 
			image={currentImage} 
			on:close={() => currentImage = false}
		/>
	{/if}
</div>
<div class="flex flex-wrap w-full gap-2">
	{#each images as image}
		<div class="w-full md:w-1/2 lg:w-1/3 xl:w-1/4 md:h-1/2 lg:w-1/3 overflow-hidden hover:cursor-pointer grow-0">
			<Image 
				src={image} 
				alt="Wedding Photo" 
				class="
					w-full h-full 
					object-cover object-[50 50] aspect-square
					transition duration-300
					scale-100
					hover:object-[0 0]
					hover:duration-[3s] 
					hover:scale-125
				"
			/>
		</div>
	{/each}
</div>