<script>
	import Image from "./image.svelte";

  export let image = 'pond-v1.jpg';
	export let title = '';
	export let subtitle = '';
  
</script>

<section class="text-gray-600 body-font w-screen h-[50vh] relative">
	<Image class="object-cover object-center w-full h-full" alt="hero" src={image} />
	<div class="absolute inset-0 bg-opacity-30 bg-white">
		<div class="container mx-auto flex px-5 py-24 items-center justify-center flex-col">
			<div class="text-center lg:w-2/3 w-full">
				<h1 class="title-font text-6xl mb-4 text-gray-900 font-thin">{title}</h1>
				<p class="mb-8 leading-relaxed text-gray-900 text-lg">{subtitle}</p>
			</div>
		</div>
	</div>
</section>

