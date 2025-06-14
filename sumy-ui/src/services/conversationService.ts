import { db } from '../firebase';
import { 
  collection, 
  addDoc, 
  query, 
  where, 
  orderBy, 
  getDocs, 
  Timestamp,
  DocumentData 
} from 'firebase/firestore';

export interface Conversation {
  id?: string;
  userId: string;
  query: string;
  response: string;
  metadata?: {
    confidence?: number;
    dish?: string;
    wine_type?: string;
    alternatives?: number;
  };
  timestamp: Date;
}

export const saveConversation = async (conversation: Omit<Conversation, 'id'>) => {
  try {
    const docRef = await addDoc(collection(db, 'conversations'), {
      ...conversation,
      timestamp: Timestamp.fromDate(conversation.timestamp)
    });
    return docRef.id;
  } catch (error) {
    console.error('Error al guardar la conversación:', error);
    throw error;
  }
};

export const getUserConversations = async (userId: string): Promise<Conversation[]> => {
  try {
    const q = query(
      collection(db, 'conversations'),
      where('userId', '==', userId),
      orderBy('timestamp', 'desc')
    );
    
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      timestamp: doc.data().timestamp.toDate()
    })) as Conversation[];
  } catch (error) {
    console.error('Error al obtener las conversaciones:', error);
    throw error;
  }
}; 