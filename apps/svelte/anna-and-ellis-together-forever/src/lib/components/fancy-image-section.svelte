<script>
	import { ImageGroup } from '$components';
	export let header;
	export let subHeader;
	export let text;
	export let imageGroupContent = {};
	export let reversed = false;
</script>

<div class="flex w-full justify-center" style={`flex-direction: ${reversed ? 'row-reverse': 'row'}`}>
	<div class="basis-1/2">
		<ImageGroup {...imageGroupContent} />
	</div>
	<div class="flex flex-col justify-center items-center basis-1/2">
		{#if header}<h2 class="text-5xl font-bold">{header}</h2>{/if}
		{#if subHeader}<h3 class="text-2xl font-semibold">{subHeader}</h3>{/if}
		{#if text}<p>{text}</p>{/if}
	</div>
</div>
