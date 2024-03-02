<script>
	import Image from "./image.svelte";

	export let header;
	export let subHeader;
	export let text;
	export let img = {};
	export let reversed = false;
</script>

<div class="flex w-full justify-center min-h-[500px] max-h-fit " style={`flex-direction: ${reversed ? 'row-reverse': 'row'}`}>
	<div class="basis-1/2 relative">
		<div class="absolute inset-0 overflow-hidden">
			<Image
				class="object-cover w-full h-full"
				src={img?.src} 
				alt={img?.alt}
			/>
		</div>
	</div>
	<div class="flex flex-col justify-center items-center basis-1/2">
		{#if header}<h2 class="text-5xl font-bold">{header}</h2>{/if}
		{#if subHeader}<h3 class="text-2xl font-semibold">{subHeader}</h3>{/if}
		{#if text}<p>{text}</p>{/if}
	</div>
</div>
