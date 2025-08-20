import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { useAuthStore } from './stores/auth';

import 'bootstrap';
import '@/assets/styles/main.css';

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);

const authStore = useAuthStore();
authStore.checkAuthOnAppStart();

app.use(router);
app.mount('#app');
