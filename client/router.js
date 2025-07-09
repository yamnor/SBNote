import * as constants from "./constants.js";

import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("./views/Home.vue"),
    },
    {
      path: "/login",
      name: "login",
      component: () => import("./views/LogIn.vue"),
      props: (route) => ({ redirect: route.query[constants.params.redirect] }),
    },
    {
      path: "/slide/:filename",
      name: "slide",
      component: () => import("./views/Slide.vue"),
      props: (route) => ({ 
        filename: route.params.filename.replace(/\.md$/, '') 
      }),
    },
    {
      path: "/mol/:filename",
      name: "mol",
      component: () => import("./views/Mol.vue"),
      props: (route) => ({ 
        filename: route.params.filename.replace(/\.md$/, '') 
      }),
    },
    {
      path: "/raw/:filename",
      name: "raw",
      component: () => import("./views/Raw.vue"),
      props: (route) => ({ 
        filename: route.params.filename.replace(/\.md$/, '') 
      }),
    },
    {
      path: "/new",
      name: "new",
      component: () => import("./views/Note.vue"),
    },
    {
      path: "/search",
      name: "search",
      component: () => import("./views/Search.vue"),
      props: (route) => ({
        searchTerm: route.query[constants.params.searchTerm],
        sortBy: Number(route.query[constants.params.sortBy]) || undefined,
      }),
    },
    {
      path: "/tag/:tagName",
      name: "tag",
      component: () => import("./views/Search.vue"),
      props: (route) => ({
        tagName: route.params.tagName,
        sortBy: Number(route.query[constants.params.sortBy]) || undefined,
      }),
    },
    {
      path: "/:filename",
      name: "note",
      component: () => import("./views/Note.vue"),
      props: (route) => ({ 
        filename: route.params.filename.replace(/\.md$/, '') 
      }),
    },
  ],
});

router.afterEach((to) => {
  let title = "SBNote";
  
  // Define view names for dynamic title updates
  const viewNames = {
    note: "Note",
    slide: "Slide", 
    mol: "Mol",
    raw: "Raw"
  };
  
  if (to.name === "note") {
    if (to.params.filename) {
      // For existing notes, we'll update the title dynamically in the Note component
      title = "Note - " + title;
    } else {
      title = "New Note - " + title;
    }
  } else if (viewNames[to.name]) {
    // For other views (slide/mol/code), we'll update the title dynamically in their components
    title = viewNames[to.name] + " - " + title;
  }
  
  document.title = title;
});

export default router;
