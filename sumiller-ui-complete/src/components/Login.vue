<template>
  <div class="login-container">
    <div v-if="!user" class="login-box">
      <h2>Bienvenido al Sumiller IA</h2>
      <button @click="signInWithGoogle" class="google-btn">
        <img src="../assets/google-icon.png" alt="Google" />
        Iniciar sesión con Google
      </button>
    </div>
    <div v-else class="user-info">
      <img :src="user.photoURL" :alt="user.displayName" class="user-avatar" />
      <span>{{ user.displayName }}</span>
      <button @click="signOut" class="logout-btn">Cerrar sesión</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup, signOut as firebaseSignOut, onAuthStateChanged, User } from 'firebase/auth';

const user = ref<User | null>(null);

onMounted(() => {
  onAuthStateChanged(auth, (newUser) => {
    user.value = newUser;
  });
});

const signInWithGoogle = async () => {
  try {
    await signInWithPopup(auth, googleProvider);
  } catch (error) {
    console.error('Error al iniciar sesión:', error);
  }
};

const signOut = async () => {
  try {
    await firebaseSignOut(auth);
  } catch (error) {
    console.error('Error al cerrar sesión:', error);
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.login-box {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.google-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: white;
  border: 1px solid #ddd;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.google-btn:hover {
  background-color: #f8f8f8;
}

.google-btn img {
  width: 24px;
  height: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.logout-btn {
  background: #ff4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.logout-btn:hover {
  background: #cc0000;
}
</style> 