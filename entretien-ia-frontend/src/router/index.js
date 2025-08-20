import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

import HomeView from '@/views/HomeView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';
import InterviewView from '@/views/InterviewView.vue';
import HistoryView from '@/views/HistoryView.vue';
import PlayerView from '@/views/PlayerView.vue';
import CreateSessionView from '@/views/recruiter/CreateSessionView.vue';
import DashboardCandidateView from '@/views/candidate/DashboardCandidateView.vue';
import DashboardRecruiterView from '@/views/recruiter/DashboardRecruiterView.vue';
import ReportView from '@/views/ReportView.vue';
import FeedbackView from '@/views/candidate/FeedbackView.vue';
import QuestionManagerView from '@/views/recruiter/QuestionManagerView.vue';
import AllQuestionsView from '@/views/admin/AllQuestionsView.vue';
import UserManagementView from '@/views/admin/UserManagementView.vue';
import ProfileView from '@/views/ProfileView.vue';
import ForgotPasswordView from '@/views/ForgotPasswordView.vue';
import ResetPasswordView from '@/views/ResetPasswordView.vue';
import ExportView from '@/views/admin/ExportView.vue';
import ConfigIAView from '@/views/admin/ConfigIAView.vue';
import DashboardAdminView from '@/views/admin/DashboardAdminView.vue';
import SystemStatusView from '@/views/admin/SystemStatusView.vue';

const routes = [
  { path: '/redirecting', name: 'post-login-redirect' },

  { path: '/', name: 'home', component: HomeView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
  { path: '/reset-password/:token', name: 'reset-password', component: ResetPasswordView, props: true },

  // Routes Protégées
  { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },

  // Routes Candidat
  { path: '/candidate/dashboard', name: 'candidate-dashboard', component: DashboardCandidateView, meta: { requiresAuth: true, roles: ['candidat'] } },
  { path: '/interview/:sessionId', name: 'interview', component: InterviewView, props: true, meta: { requiresAuth: true, roles: ['candidat'] } },
  { path: '/history', name: 'history', component: HistoryView, meta: { requiresAuth: true, roles: ['candidat'] } },
  { path: '/feedback/:id', name: 'feedback', component: FeedbackView, props: true, meta: { requiresAuth: true, roles: ['candidat'] } },

  // Routes Recruteur
  { path: '/recruiter/dashboard', name: 'recruiter-dashboard', component: DashboardRecruiterView, meta: { requiresAuth: true, roles: ['recruteur', 'admin'] } },
  { path: '/recruiter/create-session', name: 'create-session', component: CreateSessionView, meta: { requiresAuth: true, roles: ['recruteur', 'admin'] } },
  { path: '/recruiter/questions', name: 'question-manager', component: QuestionManagerView, meta: { requiresAuth: true, roles: ['recruteur', 'admin'] } },

  // Routes Admin
  { path: '/admin/dashboard', name: 'admin-dashboard', component: DashboardAdminView, meta: { requiresAuth: true, roles: ['admin'] }},
  { path: '/admin/questions', name: 'admin-questions', component: AllQuestionsView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/admin/users', name: 'user-management', component: UserManagementView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/admin/export', name: 'admin-export', component: ExportView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/admin/config-ia', name: 'admin-config-ia', component: ConfigIAView, meta: { requiresAuth: true, roles: ['admin'] } },
  {path: '/admin/status', name: 'admin-status', component: SystemStatusView, meta: { requiresAuth: true, roles: ['admin'] } },

  // Routes Partagées (Rapport, Player)
  { path: '/report/:id', name: 'report', component: ReportView, props: true, meta: { requiresAuth: true } },
  { path: '/player/:id', name: 'player', component: PlayerView, props: true, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;
  const mustChangePassword = authStore.mustChangePassword;
  const userRole = authStore.userRole;

  if (to.name === 'post-login-redirect') {
    if (!isAuthenticated) return next({ name: 'login' });

    if (mustChangePassword) return next({ name: 'profile' });

    switch (userRole) {
      case 'admin': return next({ name: 'admin-dashboard' });
      case 'recruteur': return next({ name: 'recruiter-dashboard' });
      case 'candidat': return next({ name: 'candidate-dashboard' });
      default: return next({ name: 'home' });
    }
  }

  if (isAuthenticated && mustChangePassword && to.name !== 'profile') {
    return next({ name: 'profile' });
  }

  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } });
    }
    if (to.meta.roles && !to.meta.roles.includes(userRole)) {
      alert("Accès non autorisé.");
      switch (userRole) {
        case 'admin': return next({ name: 'admin-dashboard' });
        case 'recruteur': return next({ name: 'recruiter-dashboard' });
        case 'candidat': return next({ name: 'candidate-dashboard' });
        default: return next({ name: 'home' });
      }
    }
  }

  if (isAuthenticated && ['login', 'register'].includes(to.name)) {
    switch (userRole) {
        case 'admin': return next({ name: 'admin-dashboard' });
        case 'recruteur': return next({ name: 'recruiter-dashboard' });
        case 'candidat': return next({ name: 'candidate-dashboard' });
        default: return next({ name: 'home' });
    }
  }

  return next();
});

export default router;
