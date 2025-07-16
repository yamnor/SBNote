import * as constants from "./lib/constants.js";

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
      path: "/coordinate/:filename",
      name: "coordinate",
      component: () => import("./views/Coordinate.vue"),
      props: (route) => ({ 
        filename: route.params.filename.replace(/\.md$/, '') 
      }),
    },
    {
      path: "/output/:filename",
      name: "output",
      component: () => import("./views/Output.vue"),
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
      path: "/note/:filename",
      name: "note",
      component: () => import("./views/Note.vue"),
      props: (route) => ({ 
        filename: route.params.filename.replace(/\.md$/, '') 
      }),
    },
    {
      path: "/:basename",
      name: "basename-redirect",
      beforeEnter: async (to, from, next) => {
        try {
          // Skip if basename contains dots or starts with known prefixes
          if (to.params.basename.includes('.') || 
              to.params.basename.startsWith('api') ||
              to.params.basename.startsWith('files') ||
              to.params.basename.startsWith('a') ||
              to.params.basename.startsWith('xyz') ||
              to.params.basename.startsWith('pkl') ||
              to.params.basename.startsWith('note') ||
              to.params.basename.startsWith('output') ||
              to.params.basename.startsWith('coordinate') ||
              to.params.basename.startsWith('search') ||
              to.params.basename.startsWith('tag') ||
              to.params.basename.startsWith('new') ||
              to.params.basename.startsWith('login')) {
            next({ name: 'home' });
            return;
          }
          
          // Get note data by basename using the API library
          try {
            const response = await fetch(`/api/notes/basename/${to.params.basename}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
              }
            });
            
            if (!response.ok) {
              if (response.status === 401) {
                // Authentication required, redirect to login page
                next({ name: 'login', query: { redirect: `/${to.params.basename}` } });
                return;
              } else {
                // If the note doesn't exist, redirect to home
                next({ name: 'home' });
                return;
              }
            }
            
            const note = await response.json();
            const category = note.category || 'note';
            
            // Redirect based on category
            let redirectPath;
            if (category === 'note' || category === 'image') {
              redirectPath = `/note/${to.params.basename}`;
            } else if (category === 'output') {
              redirectPath = `/output/${to.params.basename}`;
            } else if (category === 'coordinate') {
              redirectPath = `/coordinate/${to.params.basename}`;
            } else {
              redirectPath = `/note/${to.params.basename}`;
            }
            
            next({ path: redirectPath, replace: true });
          } catch (error) {
            if (error.response?.status === 401) {
              // Authentication required, redirect to login page
              next({ name: 'login', query: { redirect: `/${to.params.basename}` } });
              return;
            } else {
              // If the note doesn't exist, redirect to home
              next({ name: 'home' });
              return;
            }
          }
        } catch (error) {
          console.error('Failed to get note data:', error);
          next({ name: 'home' });
        }
      }
    },
  ],
});

router.afterEach((to) => {
  let title = "SBNote";
  
  // Define view names for dynamic title updates
  const viewNames = {
    note: "Note",
    slide: "Slide", 
    coordinate: "Coordinate",
    output: "Output"
  };
  
  if (to.name === "note") {
    if (to.params.filename) {
      // For existing notes, we'll update the title dynamically in the Note component
      title = "Note - " + title;
    } else {
      title = "New Note - " + title;
    }
  } else if (viewNames[to.name]) {
    // For other views (slide/mol), we'll update the title dynamically in their components
    title = viewNames[to.name] + " - " + title;
  }
  
  document.title = title;
});

export default router;
