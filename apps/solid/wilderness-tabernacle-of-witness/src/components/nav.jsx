import { useLocation, A } from "@solidjs/router";

export default function Nav() {
  const location = useLocation();
  const active = (path) =>
    path == location.pathname
      ? "border-sky-600"
      : "border-transparent hover:border-sky-600";
  return (
    <nav class="bg-sky-800 w-full flex justify-between items-center p-3 text-gray-200 sticky top-0">
      <p class="px-3">
        The Wilderness Tabernacle of Witness
      </p>
      <ul class="flex">
        <li class={`border-b-2 ${active("/")} mx-1.5 sm:mx-6`}>
          <A href="/">Home</A>
        </li>
        <li class={`border-b-2 ${active("/gallery")} mx-1.5 sm:mx-6`}>
          <A href="/gallery">Photo Gallery</A>
        </li>
        <li class={`border-b-2 ${active("/bible-stories")} mx-1.5 sm:mx-6`}>
          <A href="/bible-stories">Bible Stories</A>
        </li>
        <li class={`border-b-2 ${active("/new-testament")} mx-1.5 sm:mx-6`}>
          <A href="/new-testament">New Testament Translations</A>
        </li>
      </ul>
    </nav>
  );
}
