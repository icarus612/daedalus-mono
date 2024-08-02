import Components from "views/Components/Components.jsx";
import LandingPage from "views/LandingPage/LandingPage.jsx";
import ProfilePage from "views/ProfilePage/ProfilePage.jsx";
import GalleryPage from "views/ProfilePage/GalleryPage.jsx";
import LoginPage from "views/LoginPage/LoginPage.jsx";

var indexRoutes = [
  { path: "/new-testament", name: "LandingPage", component: LandingPage },
  { path: "/bible-stories", name: "ProfilePage", component: ProfilePage },
  { path: "/gallery", name: "GalleryPage", component: GalleryPage },
  { path: "/login-page", name: "LoginPage", component: LoginPage },
  { path: "/", name: "Components", component: Components }
];

export default indexRoutes;
