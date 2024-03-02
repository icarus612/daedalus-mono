<script>
	import Image from "./image.svelte";

  export let imgText = "01.";
  export let header = "24 JUNE 2022";
  export let subHeader = "THE NEXT JOURNEY";
  export let imgSrc = "default.jpg"
  export let imgAlt = "A pretty picture"
  export let imgDim = {}
  
  const { width = false, height = false } = imgDim;
</script>

<div class="space-y-4 flex flex-col items-center">
  <div class="relative">
    <div class="rounded-full overflow-hidden z-10 relative">
      <Image
        class="object-cover w-64"
        src="{imgSrc}"
        alt="{imgAlt}"
        style="
          {width && `width: ${width};`}
          {height && `width: ${height};`}
        "
      />
      <p class="text-7xl absolute text-white right-1 bottom-1 z-20">{imgText}</p>
    </div>
    <p class="text-7xl absolute text-black duration-500 right-1 bottom-1">{imgText}</p>
  </div>
  <div class="w-px h-32 bg-gradient-to-b from-gray-200 via-gray-500 to-white" />
  <div class="text-sm text-center">
    <p>{header}</p>
    <p class="font-semibold">{subHeader}</p>
  </div>
</div>