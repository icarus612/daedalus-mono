<script>
  import "$styles/tailwind.css"
  import { Header, Footer } from "$components"
</script>

<div class="flex flex-col w-full min-h-screen justify-between content-center">
  <slot name="header"><Header /></slot>
  <slot />
  <slot name="footer"><Footer /></slot>
</div>
