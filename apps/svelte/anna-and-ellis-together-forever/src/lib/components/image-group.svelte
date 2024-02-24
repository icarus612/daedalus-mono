<script>
	export let width = false;
	export let imageColumns = [
		[
			{
				src: 'images/fullrez/forever-journey.jpg',
				alt: 'Forever journey',
				height: '500px'
			},
      {
        src: 'images/fullrez/engagement.jpg',
        alt: 'Engagement',
        height: '350px'
      },
		],
		[
      {
        src: 'images/fullrez/first-date.jpg',
        alt: 'First date',
        height: '350px'
      },
			{
				src: 'images/fullrez/pond-v1.jpg',
				alt: 'First date',
				height: '300px'
			},
			{
				src: 'images/fullrez/sunny-piglet.jpg',
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
				<img
					class="rounded-full object-cover p-2"
					{src}
					{alt}
					{width}
					{height}
					style={`width: ${width}; height: ${height};`}
				/>
			{/each}
		</div>
	{/each}
</div>
