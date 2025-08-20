import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- INTERCEPTEUR POUR LA GESTION DES TOKENS ---
// Cette fonction s'exécutera avant CHAQUE requête.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore();
      console.log("Token expiré ou invalide. Déconnexion automatique.");

      authStore.logout();

      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);


export function setAuthHeader(token) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

export function removeAuthHeader() {
  delete apiClient.defaults.headers.common['Authorization'];
}


export const login = (credentials) => {
  return apiClient.post('/login', credentials);
};


export const register = (userData) => {
  return apiClient.post('/register', userData);
};


/**
 * Uploade un fichier ET les timestamps des événements pour une session.
 * @param {number} sessionId L'ID de la session.
 * @param {File} file Le fichier vidéo/audio.
 * @param {Array} events Le tableau des événements { questionId, timestamp }.
 */
export const uploadFileWithEvents = (sessionId, file, events) => {
  const formData = new FormData();
  formData.append('file', file);
  // On transforme le tableau d'événements en chaîne JSON pour l'envoyer
  formData.append('events', JSON.stringify(events));

  return apiClient.post(`/upload/${sessionId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};


export const getMySessions = () => {
  return apiClient.get('/sessions/me');
};

/**
 * Soumet et finalise une session d'entretien.
 * @param {number} sessionId L'ID de la session.
 */
export const submitSession = (sessionId) => {
  return apiClient.post(`/session/${sessionId}/submit`);
};

export const getSessionDetails = (sessionId) => {
  return apiClient.get(`/session/${sessionId}`);
};

export const getCandidates = () => {
  return apiClient.get('/users/candidates');
};

export const getCandidateDashboard = () => {
  return apiClient.get('/candidate/dashboard');
};

export const getRecruiterDashboardData = () => {
  return apiClient.get('/recruiter/dashboard');
};

export const getAdminDashboardStats = () => {
  return apiClient.get('/admin/dashboard');
};

export const createSession = (sessionData) => {
  return apiClient.post('/session/create', sessionData);
};

export const getPendingSessions = () => {
  return apiClient.get('/sessions/pending');
};

export const getSessionHistory = () => {
  return apiClient.get('/sessions/history');
};

export const getRecruiterSessions = () => {
  return apiClient.get('/recruiter/sessions');
};

export const getSessionQuestions = (sessionId) => {
  return apiClient.get(`/session/${sessionId}/questions`);
};

export const deleteSession = (sessionId) => {
  return apiClient.delete(`/session/${sessionId}`);
};

export const startAnalysis = (sessionId) => {
  return apiClient.post(`/report/generate/${sessionId}`);
};


export const getReport = (sessionId) => {
  return apiClient.get(`/report/${sessionId}`);
};


/**
 * @param {number} sessionId
 * @returns {Promise<Blob>} Une promesse qui se résout avec le Blob du fichier PDF.
 */
export const downloadPdfReport = async (sessionId) => {
  try {
    const response = await apiClient.get(`/report/${sessionId}/pdf`, {
      // On spécifie que la réponse attendue est un 'blob' (fichier binaire)
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    console.error("Erreur lors du téléchargement du PDF:", error);
    throw error;
  }
};

export const validateReport = (sessionId, commentaire) => {
  return apiClient.post(`/report/${sessionId}/validate`, { commentaire });
};

// --- Fonctions pour la Gestion des Questions du Recruteur ---

export const getRecruiterQuestions = () => {
  return apiClient.get('/recruiter/questions');
};

export const createQuestion = (questionData) => {
  return apiClient.post('/recruiter/questions', questionData);
};

export const updateQuestion = (questionId, questionData) => {
  return apiClient.put(`/recruiter/questions/${questionId}`, questionData);
};

export const deleteQuestion = (questionId) => {
  return apiClient.delete(`/recruiter/questions/${questionId}`);
};


export const getAllInspirationQuestions = () => {
  return apiClient.get('/questions/all');
};

// --- Fonctions pour la Supervision Admin ---

export const getAllQuestions = () => {
  return apiClient.get('/admin/questions/all');
};

export const signalQuestion = (questionId, signalementData) => {
  // signalementData est un objet { signalement: boolean, commentaire: string }
  return apiClient.post(`/admin/questions/signal/${questionId}`, signalementData);
};


// ...
export const createDefaultQuestion = (questionData) => apiClient.post('/admin/questions/default', questionData);
export const updateDefaultQuestion = (id, data) => apiClient.put(`/admin/questions/default/${id}`, data);
export const deleteDefaultQuestion = (id) => apiClient.delete(`/admin/questions/default/${id}`);

// --- Fonctions pour la Gestion des Utilisateurs par l'Admin ---

export const getAllUsers = () => {
  return apiClient.get('/admin/users');
};

export const createUser = (userData) => {
  return apiClient.post('/admin/users', userData);
};

export const updateUser = (userId, userData) => {
  return apiClient.put(`/admin/users/${userId}`, userData);
};

export const deleteUser = (userId) => {
  return apiClient.delete(`/admin/users/${userId}`);
};

export const updateMyProfile = (profileData) => {
  return apiClient.put('/users/profile', profileData);
};

export const forgotPassword = (email) => {
  return apiClient.post('/forgot-password', { email });
};

export const resetPassword = (token, new_password) => {
  return apiClient.post('/reset-password', { token, new_password });
};


export const runSystemTests = () => apiClient.post('/admin/system-status/run-tests');
export const getLatestSystemStatus = () => apiClient.get('/admin/system-status/latest');


export const getExportPreview = (filters) => {
  // `filters` est un objet { startDate, endDate, ... }
  // `URLSearchParams` le convertit en chaîne de requête ?key=value&...
  const params = new URLSearchParams(filters).toString();
  return apiClient.get(`/admin/export/preview?${params}`);
};

export const downloadExportCsv = async (filters) => {
  const params = new URLSearchParams(filters).toString();
  const response = await apiClient.get(`/admin/export/csv?${params}`, {
    responseType: 'blob',
  });

  // Logique pour déclencher le téléchargement
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'export_entretiens.csv');
  document.body.appendChild(link);
  link.click();
  link.remove();
};


export const getWeights = () => {
  return apiClient.get('/admin/weights');
};

export const updateWeights = (weights) => {
  return apiClient.post('/admin/weights', weights);
};


export const getProfiles = () => apiClient.get('/admin/profiles');
export const createProfile = (data) => apiClient.post('/admin/profiles', data);
export const updateProfile = (id, data) => apiClient.put(`/admin/profiles/${id}`, data);
export const deleteProfile = (id) => apiClient.delete(`/admin/profiles/${id}`);
export const getProfilesForSelection = () => apiClient.get('/profiles');



