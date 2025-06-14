<template>
  <div class="conversation-history">
    <h3>Historial de Consultas</h3>
    <div v-if="loading" class="loading">
      Cargando conversaciones...
    </div>
    <div v-else-if="conversations.length === 0" class="empty-state">
      No hay conversaciones previas
    </div>
    <div v-else class="conversations-list">
      <div v-for="conv in conversations" :key="conv.id" class="conversation-item">
        <div class="conversation-header">
          <span class="timestamp">{{ formatDate(conv.timestamp) }}</span>
        </div>
        <div class="message">
          <strong>Pregunta:</strong> {{ conv.message }}
        </div>
        <div class="response">
          <strong>Respuesta:</strong> {{ conv.response }}
        </div>
        <div v-if="conv.metadata" class="metadata">
          <small>Confianza: {{ (conv.metadata.confidence * 100).toFixed(1) }}%</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { auth } from '../firebase';
import { getUserConversations, type Conversation } from '../services/conversationService';

const conversations = ref<Conversation[]>([]);
const loading = ref(true);

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(date);
};

onMounted(async () => {
  try {
    const user = auth.currentUser;
    if (user) {
      conversations.value = await getUserConversations(user.uid);
    }
  } catch (error) {
    console.error('Error al cargar conversaciones:', error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.conversation-history {
  padding: 1rem;
  max-width: 800px;
  margin: 0 auto;
}

.loading, .empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.conversation-item {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}

.message, .response {
  margin: 0.5rem 0;
  line-height: 1.5;
}

.response {
  color: #2c3e50;
}

.metadata {
  margin-top: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}
</style> 