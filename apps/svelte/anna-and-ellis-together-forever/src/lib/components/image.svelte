
<script>
	export let src, alt;
	
	$: src = src.startsWith('/') ? src : '/' + src;
</script>

 <img  {...$$props} src={'https://storage.googleapis.com/icarus64_wedding/wedding_photos' + src} alt={alt}/>