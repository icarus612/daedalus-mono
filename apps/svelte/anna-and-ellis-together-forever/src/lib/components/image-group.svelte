<script>
	import Image from './image.svelte';
	export let imageColumns = [
		[
			{
				src: 'forever-journey.jpg',
				alt: 'Forever journey',
				height: '500px'
			},
      {
        src: 'engagement.jpg',
        alt: 'Engagement',
        height: '350px'
      },
		],
		[
      {
        src: 'first-date.jpg',
        alt: 'First date',
        height: '350px'
      },
			{
				src: 'pond-v1.jpg',
				alt: 'First date',
				height: '300px'
			},
			{
				src: 'sunny-piglet.jpg',
				alt: 'Engagement',
				height: '350px'
			}
		]
	];
</script>

<div class="flex justify-center items-center">
	{#each imageColumns as imageGroup}
		<div class="h-min">
			{#each imageGroup as { src, alt, height }}
				<Image
					class="rounded-full object-cover p-2"
					{src}
					{alt}
				/>
			{/each}
		</div>
	{/each}
</div>
