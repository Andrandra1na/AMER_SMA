import { defineStore } from 'pinia';
import * as api from '@/services/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role,
    mustChangePassword: (state) => state.user?.doit_changer_mdp || false,
  },
  actions: {
    async login(credentials) {
      try {
        const response = await api.login(credentials);
        this.setUserData(response.data);
        return { success: true };
      } catch (error) {
        console.error("Erreur dans authStore.login:", error);
        this.logout();
        return { success: false, message: error.response?.data?.msg || "Erreur de connexion." };
      }
    },

    async register(userData) {
      try {
        await api.register(userData);
        return { success: true };
      } catch (error) {
        console.error("Erreur dans authStore.register:", error);
        return { success: false, message: error.response?.data?.msg || "Erreur lors de l'inscription." };
      }
    },

    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      api.removeAuthHeader();
    },

    setUserData({ access_token, user_info }) {
      if (access_token && user_info) {
        this.token = access_token;
        this.user = user_info;
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user_info));
        api.setAuthHeader(access_token);
      }
    },

    checkAuthOnAppStart() {
      if (this.token) {
        api.setAuthHeader(this.token);
      }
    }
  },
});
